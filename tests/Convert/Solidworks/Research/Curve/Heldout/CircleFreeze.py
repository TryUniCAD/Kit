from __future__ import annotations

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.Fields.WriterFreeze import VerifyFreeze
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# earlier circle sources must remain independent of the unchanged measured writer and request adapter
def VerifyCurves(SourceRoot: FilePath = KRepoRoot) -> dict[str, object]:
    BaseFreeze = VerifyFreeze(SourceRoot)
    FreezePath = KRepoRoot / "re/solidworks/v2026/heldout/CurveCircleWriterFreeze.json"
    assert HashBytes(FreezePath.read_bytes()).hexdigest() == (
        "4a6cb20e311fa1572b234f12b4fb3dfdd672b5095ca147268bb410d76c5694f7"
    )
    Freeze = ReadObject(FreezePath)
    assert BaseFreeze["measured_writer_revision"] == Freeze["measured_writer_revision"]
    assert Freeze["schema"] == "kit.sw2026.curve-circle-writer-freeze.v1"
    assert Freeze["heldout_native_payloads_inspected"] is False
    BasePath = KRepoRoot / CastValue(str, Freeze["base_freeze_path"])
    assert HashBytes(BasePath.read_bytes()).hexdigest() == Freeze["base_freeze_sha256"]
    for Entry in CastValue(list[dict[str, object]], Freeze["additional_files"]):
        SourcePath = SourceRoot / CastValue(str, Entry["path"])
        assert not SourcePath.is_symlink()
        assert SourcePath.resolve().is_relative_to(SourceRoot.resolve())
        RawValue = SourcePath.read_bytes()
        assert len(RawValue) == Entry["bytes"]
        assert HashBytes(RawValue).hexdigest() == Entry["sha256"]
    LockPath = KRepoRoot / "re/solidworks/v2026/heldout/CurveSourceLock.json"
    assert (
        HashBytes(LockPath.read_bytes()).hexdigest()
        == Freeze["curve_source_lock_sha256"]
    )
    SourceLock = ReadObject(LockPath)
    SpecsPath = KRepoRoot / "re/tooling/sw2026/CurveSpecs.json"
    assert HashBytes(SpecsPath.read_bytes()).hexdigest() == SourceLock["specs_sha256"]
    assert SourceLock["specs_sha256"] == Freeze["curve_specs_sha256"]
    Heldouts = [
        Entry
        for Entry in CastValue(list[dict[str, object]], SourceLock["cases"])
        if Entry["split"] == "heldout"
    ]
    Evaluated = CastValue(list[dict[str, object]], Freeze["evaluated_heldouts"])
    Names = {Entry["name"] for Entry in Evaluated}
    assert len(Heldouts) == 6 and len(Evaluated) == 2
    assert Evaluated == [Entry for Entry in Heldouts if Entry["name"] in Names]
    return Freeze
