from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.EncoderRoundTrip.RunEncoder import RunEncoder


# invalid driving values must fail before publishing any research scope or candidate
@TestMark.parametrize("DepthValue", ("0", "-1", "nan", "inf"))
def CheckBadDepth(TmpPath: FilePath, DepthValue: str) -> None:
    SourcePath = TmpPath / "Invalid.SLDPRT"
    _ = SourcePath.write_bytes(b"invalid native input")
    OutputPath = TmpPath / "Rejected"
    Result = RunEncoder(TmpPath, "solidworks", SourcePath, OutputPath, DepthValue)
    assert Result.returncode == 1, Result.stderr
    assert not OutputPath.exists()
    assert not list(TmpPath.glob(".encoder-round-trip-*"))
