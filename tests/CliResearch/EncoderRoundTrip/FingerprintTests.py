from hashlib import sha256 as HashContent
from pathlib import Path as FilePath

from tests.CliResearch.EncoderRoundTrip.FreshCuboid import FreshCuboid
from tests.CliResearch.EncoderRoundTrip.ReadReplayPins import ReadReplayPins
from tests.CliResearch.EncoderRoundTrip.RunEncoder import RunEncoder


# repeated independent processes must retain identical decoded evidence and deterministic run identities
def CheckReplayPins(TmpPath: FilePath) -> None:
    SourcePath = TmpPath / "Source.f3d"
    SourceBytes = FreshCuboid(SourcePath, (23.4, 17.8, 5.3))
    SourceSha = HashContent(SourceBytes).hexdigest()
    FirstPath, SecondPath = TmpPath / "First", TmpPath / "Second"
    for OutputPath in (FirstPath, SecondPath):
        Result = RunEncoder(
            TmpPath,
            "fusion",
            SourcePath,
            OutputPath,
            "14.2",
            LocatorValue=r"C:\KitEncoderRoundTrip",
        )
        assert Result.returncode == 0, Result.stdout + Result.stderr
    assert ReadReplayPins(FirstPath, SourceSha) == ReadReplayPins(SecondPath, SourceSha)
    assert (FirstPath / "document.json").read_bytes() == (
        SecondPath / "document.json"
    ).read_bytes()
    assert SourcePath.read_bytes() == SourceBytes
