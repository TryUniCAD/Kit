from hashlib import sha256 as HashContent
from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.EncoderRoundTrip.FreshCuboid import FreshCuboid
from tests.CliResearch.EncoderRoundTrip.RunEncoder import RunEncoder


# deterministic refusal cannot demonstrate reproducible candidate bytes across processes
def ReadReplayPins(OutputPath: FilePath, SourceSha: str) -> dict[str, str]:
    Manifest = DecodeJson((OutputPath / "manifest.json").read_bytes())
    assert Manifest["status"] == "awaiting_native"
    assert Manifest["source"]["status"] == "decoded"
    assert Manifest["source_sha256"] == SourceSha
    assert Manifest["models_used"] is False
    NeutralSha = HashContent((OutputPath / "document.json").read_bytes()).hexdigest()
    assert Manifest["neutral_sha256"] == NeutralSha
    RunFingerprint = Manifest["run_fingerprint"]
    assert isinstance(RunFingerprint, str) and RunFingerprint
    PinValues = {"run_fingerprint": RunFingerprint, "neutral_sha256": NeutralSha}
    for RoleName in ("reconstruction", "edited"):
        RoleResult = Manifest[RoleName]
        assert RoleResult["status"] == "awaiting_native"
        CandidateSha = Manifest["candidate_sha256"][RoleName]
        assert isinstance(CandidateSha, str)
        NativePath = OutputPath / (RoleName + ".f3d")
        assert CandidateSha == HashContent(NativePath.read_bytes()).hexdigest()
        assert RoleResult["artifact"]["sha256"] == CandidateSha
        PinValues[RoleName] = CandidateSha
    return PinValues


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
