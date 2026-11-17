from __future__ import annotations

from hashlib import sha256 as HashBytes
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# prospective predictions may use only the public requests locked before the corrected serializer
def ReadFrameCase() -> tuple[dict[str, object], list[dict[str, object]]]:
    FreezePath = KRepoRoot / "re/solidworks/v2026/heldout/FrameWriterFreeze.json"
    assert HashBytes(FreezePath.read_bytes()).hexdigest() == (
        "7e80a951824e9c8e2b86e645d6326fa6a16c208d4f79a6598262c8192c8913f2"
    )
    Freeze = ReadObject(FreezePath)
    assert Freeze["schema"] == "kit.sw2026.frame-writer-freeze.v1"
    assert Freeze["constructor_dependency_count"] == 3452
    assert Freeze["heldout_native_payloads_inspected_before_freeze"] is False
    assert Freeze["private_api_observations_inspected_before_freeze"] is False
    LockPath = KRepoRoot / CastValue(str, Freeze["source_lock_path"])
    SpecPath = KRepoRoot / CastValue(str, Freeze["specs_path"])
    assert HashBytes(LockPath.read_bytes()).hexdigest() == Freeze["source_lock_sha256"]
    assert HashBytes(SpecPath.read_bytes()).hexdigest() == Freeze["specs_sha256"]
    Source = ReadObject(LockPath)
    Specs = ReadObject(SpecPath)
    assert Source["passed"] is Source["controls_healthy"] is True
    assert Source["cases"] == Freeze["evaluated_heldouts"]
    assert Source["specs_sha256"] == Freeze["specs_sha256"]
    assert Source["payload_and_api_observations_sealed_until_writer_freeze"] is True
    Cases = CastValue(list[dict[str, object]], Specs["cases"])
    assert [Value["name"] for Value in Cases] == ["F01TopFrame", "F02RightFrame"]
    assert [Value["plane"] for Value in Cases] == ["top", "right"]
    assert all(Value["split"] == "heldout" for Value in Cases)
    return {
        "source_revision": Freeze["writer_revision"],
        "source_tree": Freeze["writer_tree"],
        "source_file_count": Freeze["constructor_dependency_count"],
        "files": Freeze["files"],
    }, Cases
