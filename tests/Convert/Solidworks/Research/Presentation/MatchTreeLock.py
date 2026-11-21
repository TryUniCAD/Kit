from __future__ import annotations

from hashlib import sha256 as HashBytes
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# independently authored native cases must precede implementation and remain sealed through frozen prediction
def MatchTreeLock(Freeze: dict[str, object]) -> None:
    SourcePath = KRepoRoot / CastValue(str, Freeze["source_lock_path"])
    assert (
        HashBytes(SourcePath.read_bytes()).hexdigest() == Freeze["source_lock_sha256"]
    )
    SourceLock = ReadObject(SourcePath)
    assert SourceLock["schema"] == "kit.sw2026.unseen-tree-source-lock.v1"
    assert SourceLock["passed"] is SourceLock["controls_healthy"] is True
    assert SourceLock["postflight_no_cad_process"] is True
    assert SourceLock["license_process_ids_unchanged"] is True
    assert SourceLock["presentation_writer_started_before_lock"] is False
    assert (
        SourceLock["private_model_observations_inspected_before_writer_freeze"] is False
    )
    assert SourceLock["source_revision"] == Freeze["source_author_revision"]
    assert SourceLock["cases"] == Freeze["evaluated_heldouts"]
    SpecsPath = KRepoRoot / CastValue(str, Freeze["specs_path"])
    assert HashBytes(SpecsPath.read_bytes()).hexdigest() == Freeze["specs_sha256"]
    assert SourceLock["specs_sha256"] == Freeze["specs_sha256"]
