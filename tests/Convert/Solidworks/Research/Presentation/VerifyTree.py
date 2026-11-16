from __future__ import annotations

from hashlib import sha256 as HashBytes

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject
from tests.Convert.Solidworks.Research.Presentation.MatchTreeFiles import MatchTreeFiles
from tests.Convert.Solidworks.Research.Presentation.MatchTreeLock import MatchTreeLock


# the prospective freeze must stay immutable while independent predictions run before reference access
def VerifyTree() -> dict[str, object]:
    FreezePath = KRepoRoot / "re/solidworks/v2026/heldout/TreeWriterFreeze.json"
    assert HashBytes(FreezePath.read_bytes()).hexdigest() == (
        "df4a70bb18a6ec7c58f3d975a86d0234f6b7508d086e4a36b4dffa199d2ac17a"
    )
    Freeze = ReadObject(FreezePath)
    assert Freeze["schema"] == "kit.sw2026.tree-writer-freeze.v1"
    assert Freeze["writer_revision"] == "d5019da136433cf3b07dd8c53ee4a708950ad353"
    assert Freeze["heldout_native_payloads_inspected_before_freeze"] is False
    assert Freeze["private_api_observations_inspected_before_freeze"] is False
    MatchTreeFiles(Freeze)
    MatchTreeLock(Freeze)
    return Freeze
