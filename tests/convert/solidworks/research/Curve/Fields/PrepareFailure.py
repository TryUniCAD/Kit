from __future__ import annotations

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from typing import cast as CastValue
from tests.convert.solidworks.research.Curve.CorpusPaths import KCurveCorpus


# negative process cases must remain bound to actual prepared fixtures and explicit expected inputs
def PrepareFailure(
    TmpPath: FilePath, FailureKind: str, Entries: dict[str, dict[str, object]]
) -> tuple[str, str, dict[str, str]]:
    StreamName = "Contents/Config-0"
    Pattern = str(KCurveCorpus / "*.SLDPRT")
    Expected = {
        FileName: CastValue(str, Entry["sha256"]) for FileName, Entry in Entries.items()
    }
    if FailureKind == "EmptyPattern":
        Pattern = str(TmpPath / "Unmatched" / "*.SLDPRT")
        Expected = {}
    elif FailureKind == "MissingStream":
        StreamName = "Contents/FieldInventoryMissing"
        assert all(
            Stream["name"] != StreamName
            for Entry in Entries.values()
            for Stream in CastValue(list[dict[str, object]], Entry["streams"])
        )
    else:
        assert FailureKind == "TruncatedFixture"
        SourcePath = KCurveCorpus / "ControlRectangle.SLDPRT"
        Truncated = SourcePath.read_bytes()[:64]
        assert len(Truncated) == 64 < SourcePath.stat().st_size
        InputPath = TmpPath / "Truncated.SLDPRT"
        with InputPath.open("xb") as OutputFile:
            assert OutputFile.write(Truncated) == 64
        Pattern = str(InputPath)
        Expected = {InputPath.name: HashBytes(Truncated).hexdigest()}
    return Pattern, StreamName, Expected
