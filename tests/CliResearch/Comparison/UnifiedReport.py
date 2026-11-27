from hashlib import sha256 as HashBytes
from json import loads as DecodeJson
from pathlib import Path as FilePath
from typing import cast as CastValue


# excluded pairs must keep their detailed reports and available input pins for inspection
def CheckPairProof(
    Output: FilePath, PairRows: list[dict[str, object]], Original: dict[FilePath, bytes]
) -> None:
    for PairRow in PairRows:
        Evidence = CastValue(dict[str, object], PairRow["report"])
        ReportPath = CastValue(str, Evidence["path"])
        ReportBytes = (Output / ReportPath).read_bytes()
        assert HashBytes(ReportBytes).hexdigest() == Evidence["sha256"]
        assert len(ReportBytes) == Evidence["size_bytes"]
        Report = DecodeJson(ReportBytes)
        assert Report["pair_id"] == PairRow["id"]
        assert Report["status"] == PairRow["status"]
        InputPins = CastValue(dict[str, str], PairRow["input_sha256"])
        InputPaths = CastValue(dict[str, str | None], PairRow["inputs"])
        assert Report["input_sha256"] == InputPins
        PairName = CastValue(str, PairRow["id"])
        for SideName, FolderName in (("left", "SolidWorks"), ("right", "Fusion")):
            InputPath = Output.parent / FolderName / PairName
            if InputPath in Original:
                Digest = HashBytes(Original[InputPath]).hexdigest()
                assert InputPins[SideName] == Digest
                SourcePath = InputPaths[SideName]
                assert SourcePath is not None and FilePath(SourcePath) == InputPath
            else:
                assert SideName not in InputPins
                assert InputPaths[SideName] is None
