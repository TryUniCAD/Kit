from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Camera.CameraFreeze import VerifyCamera
from tests.Convert.Solidworks.Research.Camera.CheckViewCase import CheckViewCase
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject
from tests.Convert.Solidworks.Research.Frozen.FrozenRoot import FrozenRoot


# historical camera evidence must stay pinned while current code proves identical complete output
def TestHeldViews() -> None:
    with FrozenRoot() as SourceRoot:
        Freeze = VerifyCamera(SourceRoot)
        Specs = ReadObject(KRepoRoot / "re/tooling/sw2026/ViewSourceSpecs.json")
        Cases = CastValue(list[dict[str, object]], Specs["cases"])
        Locked = CastValue(list[dict[str, object]], Freeze["evaluated_heldouts"])
        assert len(Cases) == len(Locked) == 2
        assert {Value["name"] for Value in Cases} == {Value["name"] for Value in Locked}
        for CaseValue in Cases:
            CheckViewCase(CaseValue, SourceRoot)
        assert VerifyCamera(SourceRoot) == Freeze
