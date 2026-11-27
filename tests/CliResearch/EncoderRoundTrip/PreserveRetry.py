from hashlib import sha256 as HashContent
from pathlib import Path as FilePath

from tests.CliResearch.EncoderRoundTrip.RunEncoder import RunEncoder


# settled no op evidence must remain immutable when callers retry the same output directory
def PreserveRetry(
    TmpPath: FilePath,
    SourcePath: FilePath,
    OutputPath: FilePath,
    EditedHeight: float,
) -> None:
    Snapshot = {
        Entry.name: HashContent(Entry.read_bytes()).hexdigest()
        for Entry in OutputPath.iterdir()
    }
    Retried = RunEncoder(TmpPath, "fusion", SourcePath, OutputPath, str(EditedHeight))
    assert Retried.returncode == 1, Retried.stderr
    assert Snapshot == {
        Entry.name: HashContent(Entry.read_bytes()).hexdigest()
        for Entry in OutputPath.iterdir()
    }
