from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.EncoderRoundTrip.AlterWriter import AlterWriter
from tests.CliResearch.EncoderRoundTrip.RebindWriter import RebindWriter
from tests.CliResearch.ResearchClient import ResearchCli


# receipt attachment must bind each durable writer input to its role despite recomputed custody hashes
def VerifyInputBind(
    TmpPath: FilePath, OutputPath: FilePath, ReceiptPath: FilePath
) -> None:
    Original = {Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()}
    ReceiptBytes = ReceiptPath.read_bytes()
    for CaseName in ("Role", "Depth"):
        TamperedPath = TmpPath / ("TamperedWriter" + CaseName)
        TamperedPath.mkdir()
        for FileName, Content in Original.items():
            _ = (TamperedPath / FileName).write_bytes(Content)
        Payload = (
            Original["reconstruction-writer-input.json"]
            if CaseName == "Role"
            else AlterWriter(Original["edited-writer-input.json"])
        )
        RebindWriter(TamperedPath, Payload)
        Snapshot = {Entry.name: Entry.read_bytes() for Entry in TamperedPath.iterdir()}
        Result = ResearchCli(
            TmpPath,
            "encoder-round-trip",
            "attach-receipt",
            "--output",
            str(TamperedPath),
            "--role",
            "edited",
            "--receipt",
            str(ReceiptPath),
        )
        assert Result.returncode == 1, Result.stdout + Result.stderr
        assert (
            DecodeJson(Result.stderr)["error"]
            == "round-trip role edited writer input does not reproduce its native candidate"
        )
        assert {
            Entry.name: Entry.read_bytes() for Entry in TamperedPath.iterdir()
        } == Snapshot
    assert ReceiptPath.read_bytes() == ReceiptBytes
    assert {
        Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()
    } == Original
