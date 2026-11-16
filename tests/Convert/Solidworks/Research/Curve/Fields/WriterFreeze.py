from __future__ import annotations

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# independent heldout evidence requires the complete measured writer to remain unchanged
def VerifyFreeze(SourceRoot: FilePath = KRepoRoot) -> dict[str, object]:
    FreezePath = KRepoRoot / "re/solidworks/v2026/heldout/EndConditionWriterFreeze.json"
    assert HashBytes(FreezePath.read_bytes()).hexdigest() == (
        "fb208a5b8dd8cf9e033ad8450fd466e9754cf6374dc88bce68ee1bcd709a2918"
    )
    Freeze = ReadObject(FreezePath)
    assert Freeze["schema"] == "kit.sw2026.end-writer-freeze.v1"
    assert Freeze["heldout_native_payloads_inspected_before_freeze"] is False
    for Entry in CastValue(list[dict[str, object]], Freeze["files"]):
        SourcePath = SourceRoot / CastValue(str, Entry["path"])
        assert not SourcePath.is_symlink()
        assert SourcePath.resolve().is_relative_to(SourceRoot.resolve())
        RawValue = SourcePath.read_bytes()
        assert len(RawValue) == Entry["bytes"]
        assert HashBytes(RawValue).hexdigest() == Entry["sha256"]
    LockPath = KRepoRoot / "re/solidworks/v2026/heldout/EndConditionSourceLock.json"
    assert HashBytes(LockPath.read_bytes()).hexdigest() == Freeze["source_lock_sha256"]
    SourceLock = ReadObject(LockPath)
    SpecsPath = KRepoRoot / "re/tooling/sw2026/EndConditionSpecs.json"
    assert HashBytes(SpecsPath.read_bytes()).hexdigest() == SourceLock["specs_sha256"]
    assert Freeze["heldout_inputs"] == [
        Entry
        for Entry in CastValue(list[dict[str, object]], SourceLock["cases"])
        if Entry["split"] == "heldout"
    ]
    return Freeze
