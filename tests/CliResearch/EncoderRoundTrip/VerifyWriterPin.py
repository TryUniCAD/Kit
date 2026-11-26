from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.ResearchClient import ResearchCli


# receipt intake must verify the declared writer inputs for both roles
def VerifyWriterPin(
    TmpPath: FilePath, OutputPath: FilePath, ReceiptPath: FilePath
) -> None:
    Original = {Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()}
    TamperedPath = TmpPath / "TamperedWriter"
    TamperedPath.mkdir()
    WriterName = "reconstruction-writer-input.json"
    Snapshot = {**Original, WriterName: Original[WriterName] + b"\n"}
    for FileName, Content in Snapshot.items():
        _ = (TamperedPath / FileName).write_bytes(Content)
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
    assert DecodeJson(Result.stderr)["error"] == (
        "reconstruction-writer-input.json bytes do not match the round-trip manifest"
    )
    assert {
        Entry.name: Entry.read_bytes() for Entry in TamperedPath.iterdir()
    } == Snapshot
    assert {
        Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()
    } == Original
