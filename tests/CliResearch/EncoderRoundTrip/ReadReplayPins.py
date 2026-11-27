from hashlib import sha256 as HashContent
from json import loads as DecodeJson
from pathlib import Path as FilePath


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
