from hashlib import sha256 as HashContent
from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.EncoderRoundTrip.RunEncoder import RunEncoder
from tests.CliResearch.ResearchRoot import ResearchRoot


# repeated independent processes must retain identical decoded evidence and deterministic run identities
def CheckReplayPins(TmpPath: FilePath) -> None:
    SourcePath = (
        ResearchRoot()
        / "re/Fusion/LocalOracle/NativePublicAdapter/SavedCuboid.f3d"
    )
    FirstPath, SecondPath = TmpPath / "First", TmpPath / "Second"
    for OutputPath in (FirstPath, SecondPath):
        Result = RunEncoder(
            TmpPath, "fusion", SourcePath, OutputPath,
            LocatorValue=r"C:\KitEncoderRoundTrip",
        )
        assert Result.returncode in (0, 3), Result.stderr
    FirstRun = DecodeJson((FirstPath / "manifest.json").read_bytes())
    SecondRun = DecodeJson((SecondPath / "manifest.json").read_bytes())
    assert FirstRun["source"]["status"] == SecondRun["source"]["status"] == "decoded"
    assert FirstRun["source_sha256"] == HashContent(SourcePath.read_bytes()).hexdigest()
    for FieldName in ("run_fingerprint", "neutral_sha256", "candidate_sha256"):
        assert FirstRun[FieldName] == SecondRun[FieldName]
    assert (FirstPath / "document.json").read_bytes() == (SecondPath / "document.json").read_bytes()
    assert FirstRun["neutral_sha256"] == HashContent((FirstPath / "document.json").read_bytes()).hexdigest()
    assert FirstRun["models_used"] is SecondRun["models_used"] is False
