from json import loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.EncoderRoundTrip.RunEncoder import RunEncoder


# invalid native inputs must retain explicit failed scope without claiming application acceptance
@TestMark.parametrize(
    "Application,Extension", (("solidworks", ".SLDPRT"), ("fusion", ".f3d"))
)
def CheckBadSource(TmpPath: FilePath, Application: str, Extension: str) -> None:
    SourcePath = TmpPath / ("Invalid" + Extension)
    _ = SourcePath.write_bytes(b"this is not a native cad document")
    OutputPath = TmpPath / "Refused"
    Result = RunEncoder(TmpPath, Application, SourcePath, OutputPath)
    assert Result.returncode == 3, Result.stderr
    Manifest = DecodeJson((OutputPath / "manifest.json").read_bytes())
    assert Manifest["status"] == "incomplete"
    assert Manifest["source"]["status"] == "rejected"
    assert Manifest["reconstruction"]["status"] == "blocked"
    assert Manifest["edited"]["status"] == "blocked"
    assert Manifest["models_used"] is False
    assert Manifest["vendor_loadable"] is False
    assert Manifest["application_usable"] is False
    assert not (OutputPath / "document.json").exists()
