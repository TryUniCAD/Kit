from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.EncoderRoundTrip.RunEncoder import RunEncoder


# research publication must preserve an occupied destination before reading malformed native data
@TestMark.parametrize("CaseName", ("directory", "file"))
def CheckOccupied(TmpPath: FilePath, CaseName: str) -> None:
    SourcePath = TmpPath / "Invalid.SLDPRT"
    _ = SourcePath.write_bytes(b"invalid native input")
    OutputPath = TmpPath / "Occupied"
    if CaseName == "directory":
        OutputPath.mkdir()
        KeptPath = OutputPath / "Sentinel.bin"
    else:
        KeptPath = OutputPath
    _ = KeptPath.write_bytes(b"preserved user output")
    Result = RunEncoder(TmpPath, "solidworks", SourcePath, OutputPath)
    assert Result.returncode == 1, Result.stderr
    assert KeptPath.read_bytes() == b"preserved user output"
    assert not (OutputPath / "manifest.json").exists()
    assert not list(TmpPath.glob(".encoder-round-trip-*"))
