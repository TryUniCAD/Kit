from __future__ import annotations

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Camera.CheckViewFiles import CheckViewFiles
from tests.Convert.Solidworks.Research.Curve.Fields.WriterFreeze import VerifyFreeze
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# unseen camera results require every generating dependency to remain fixed before reference access
def VerifyCamera(SourceRoot: FilePath = KRepoRoot) -> dict[str, object]:
    BaseFreeze = VerifyFreeze(SourceRoot)
    FreezePath = KRepoRoot / "re/solidworks/v2026/heldout/ViewWriterFreeze.json"
    assert HashBytes(FreezePath.read_bytes()).hexdigest() == (
        "8d02f3956b5af5fcf4f3495b062bb6b0ce3629fe78c33f7d7ce99da0fc99edba"
    )
    Freeze = ReadObject(FreezePath)
    assert Freeze["schema"] == "kit.sw2026.camera-writer-freeze.v1"
    assert Freeze["heldout_native_payloads_inspected_before_freeze"] is False
    assert Freeze["private_api_observations_inspected_before_freeze"] is False
    CheckViewFiles(Freeze, BaseFreeze, SourceRoot)
    LockPath = KRepoRoot / CastValue(str, Freeze["source_lock_path"])
    assert HashBytes(LockPath.read_bytes()).hexdigest() == Freeze["source_lock_sha256"]
    SourceLock = ReadObject(LockPath)
    assert SourceLock["passed"] is SourceLock["controls_healthy"] is True
    assert SourceLock["postflight_no_cad_process"] is True
    assert SourceLock["license_process_ids_unchanged"] is True
    assert SourceLock["camera_writer_started_before_lock"] is False
    assert Freeze["evaluated_heldouts"] == SourceLock["cases"]
    SpecsPath = KRepoRoot / CastValue(str, Freeze["specs_path"])
    assert HashBytes(SpecsPath.read_bytes()).hexdigest() == Freeze["specs_sha256"]
    return Freeze
