from json import loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.EncoderRoundTrip.ReplayRole import ReplayRole


# isolated replay custody must preserve the published artifacts after the original archive disappears
def ReplayFusion(
    SourcePath: FilePath,
    OutputPath: FilePath,
    RoleNames: tuple[str, ...],
) -> None:
    Snapshot = {Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()}
    Manifest = DecodeJson(Snapshot["manifest.json"])
    assert Manifest["schema"] == 2
    if "edited" not in RoleNames:
        assert Manifest["writer_input_sha256"]["edited"] is None
        assert "writer_input" not in Manifest["edited"]
        assert "edited-writer-input.json" not in Snapshot
    assert SourcePath.is_file() and SourcePath.parent == OutputPath.parent
    SourcePath.unlink()
    assert not SourcePath.exists()
    for RoleName in RoleNames:
        ReplayPath = OutputPath.parent / (RoleName + "-replay")
        ReplayPath.mkdir()
        ReplayRole(ReplayPath, Snapshot, RoleName)
    assert not SourcePath.exists()
    assert {
        Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()
    } == Snapshot
