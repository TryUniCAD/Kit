from hashlib import sha256 as HashContent
from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.EncoderRoundTrip.EmitFusionRole import EmitFusionRole


# every completed role must reproduce exactly the archive pinned by its manifest from its own constructor document
def ReplayRole(ReplayPath: FilePath, Snapshot: dict[str, bytes], RoleName: str) -> None:
    Manifest = DecodeJson(Snapshot["manifest.json"])
    Artifact = Manifest[RoleName]["writer_input"]
    assert Artifact["path"] == RoleName + "-writer-input.json"
    InputBytes = Snapshot[Artifact["path"]]
    assert len(InputBytes) == Artifact["bytes"]
    assert (
        HashContent(InputBytes).hexdigest()
        == Artifact["sha256"]
        == Manifest["writer_input_sha256"][RoleName]
    )
    Prepared = DecodeJson(InputBytes)
    assert Prepared["source"] == DecodeJson(Snapshot["document.json"])["source"]
    assert set(Prepared["metadata"]) == {"fusion.authoring"}
    assert b'"$bytes"' not in InputBytes
    InputPath = ReplayPath / Artifact["path"]
    _ = InputPath.write_bytes(InputBytes)
    CandidateBytes = EmitFusionRole(
        InputPath, Manifest["native_locators"][RoleName], Manifest["written_at"]
    )
    assert CandidateBytes == Snapshot[RoleName + ".f3d"]
    assert (
        HashContent(CandidateBytes).hexdigest()
        == Manifest["candidate_sha256"][RoleName]
    )
    assert InputPath.read_bytes() == InputBytes
