from pathlib import Path as FilePath

from tests.CliResearch.EncoderRoundTrip.RunEncoder import RunEncoder


# rerunning a settled scope must preserve its recorded failure and never overwrite evidence
def CheckSettledRetry(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "Invalid.SLDPRT"
    _ = SourcePath.write_bytes(b"invalid native input")
    OutputPath = TmpPath / "Settled"
    FirstRun = RunEncoder(TmpPath, "solidworks", SourcePath, OutputPath)
    assert FirstRun.returncode == 3, FirstRun.stderr
    Snapshot = {
        Entry.relative_to(OutputPath): Entry.read_bytes()
        for Entry in OutputPath.rglob("*")
        if Entry.is_file()
    }
    SecondRun = RunEncoder(TmpPath, "solidworks", SourcePath, OutputPath)
    assert SecondRun.returncode == 1, SecondRun.stderr
    assert Snapshot == {
        Entry.relative_to(OutputPath): Entry.read_bytes()
        for Entry in OutputPath.rglob("*")
        if Entry.is_file()
    }
    assert not list(TmpPath.glob(".encoder-round-trip-*"))
