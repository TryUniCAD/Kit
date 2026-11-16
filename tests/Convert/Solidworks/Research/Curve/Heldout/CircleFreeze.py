from __future__ import annotations

from hashlib import sha256 as HashBytes
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.Fields.WriterFreeze import VerifyFreeze
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# earlier circle sources must remain independent of the unchanged measured writer and request adapter
def VerifyCircleFreeze() -> dict[str, object]:
    VerifyFreeze()
    FreezePath = KRepoRoot / "re/solidworks/v2026/heldout/CurveCircleWriterFreeze.json"
    assert HashBytes(FreezePath.read_bytes()).hexdigest() == (
        "4a6cb20e311fa1572b234f12b4fb3dfdd672b5095ca147268bb410d76c5694f7"
    )
    Freeze = ReadObject(FreezePath)
    assert Freeze["schema"] == "kit.sw2026.curve-circle-writer-freeze.v1"
    assert Freeze["heldout_native_payloads_inspected"] is False
    BasePath = KRepoRoot / CastValue(str, Freeze["base_freeze_path"])
    assert HashBytes(BasePath.read_bytes()).hexdigest() == Freeze["base_freeze_sha256"]
    for Entry in CastValue(list[dict[str, object]], Freeze["additional_files"]):
        SourcePath = KRepoRoot / CastValue(str, Entry["path"])
        assert not SourcePath.is_symlink()
        assert SourcePath.resolve().is_relative_to(KRepoRoot.resolve())
        RawValue = SourcePath.read_bytes()
        assert len(RawValue) == Entry["bytes"]
        assert HashBytes(RawValue).hexdigest() == Entry["sha256"]
    LockPath = KRepoRoot / "re/solidworks/v2026/heldout/CurveSourceLock.json"
    assert (
        HashBytes(LockPath.read_bytes()).hexdigest()
        == Freeze["curve_source_lock_sha256"]
    )
    Lock = ReadObject(LockPath)
    SpecsPath = KRepoRoot / "re/tooling/sw2026/CurveSpecs.json"
    assert HashBytes(SpecsPath.read_bytes()).hexdigest() == Lock["specs_sha256"]
    assert Lock["specs_sha256"] == Freeze["curve_specs_sha256"]
    Heldouts = [
        Entry
        for Entry in CastValue(list[dict[str, object]], Lock["cases"])
        if Entry["split"] == "heldout"
    ]
    Evaluated = CastValue(list[dict[str, object]], Freeze["evaluated_heldouts"])
    Names = {Entry["name"] for Entry in Evaluated}
    assert len(Heldouts) == 6 and len(Evaluated) == 2
    assert Evaluated == [Entry for Entry in Heldouts if Entry["name"] in Names]
    return Freeze
