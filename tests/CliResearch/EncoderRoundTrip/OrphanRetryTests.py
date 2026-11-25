from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.EncoderRoundTrip.RunEncoder import RunEncoder


# abandoned private staging must not prevent a new process from recording its own outcome
def CheckOrphanRetry(TmpPath: FilePath) -> None:
    StagePath = TmpPath / ".encoder-round-trip-abandoned"
    StagePath.mkdir()
    _ = (StagePath / "Partial.bin").write_bytes(b"unpublished evidence")
    SourcePath = TmpPath / "Invalid.SLDPRT"
    _ = SourcePath.write_bytes(b"invalid native input")
    OutputPath = TmpPath / "Retried"
    Result = RunEncoder(TmpPath, "solidworks", SourcePath, OutputPath)
    assert Result.returncode == 3, Result.stderr
    assert (
        DecodeJson((OutputPath / "manifest.json").read_bytes())["status"]
        == "incomplete"
    )
    assert (StagePath / "Partial.bin").read_bytes() == b"unpublished evidence"
    assert list(StagePath.iterdir()) == [StagePath / "Partial.bin"]
