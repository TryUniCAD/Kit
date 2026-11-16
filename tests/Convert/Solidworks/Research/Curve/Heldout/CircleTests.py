from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.Heldout.CheckCircleCase import (
    CheckCircleCase,
)
from tests.Convert.Solidworks.Research.Curve.Heldout.CircleFreeze import VerifyCurves
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject
from tests.Convert.Solidworks.Research.Frozen.FrozenRoot import FrozenRoot


# historical circle evidence must remain tied to unchanged source while current outputs are compared independently
def TestCircleHold() -> None:
    with FrozenRoot() as SourceRoot:
        Freeze = VerifyCurves(SourceRoot)
        Specs = ReadObject(KRepoRoot / "re/tooling/sw2026/CurveSpecs.json")
        Cases = [
            Entry
            for Entry in CastValue(list[dict[str, object]], Specs["cases"])
            if Entry["split"] == "heldout"
            and CastValue(dict[str, object], Entry["profile"])["kind"] == "circle"
        ]
        Locked = CastValue(list[dict[str, object]], Freeze["evaluated_heldouts"])
        assert len(Cases) == len(Locked) == 2
        assert {Entry["name"] for Entry in Cases} == {Entry["name"] for Entry in Locked}
        for CaseValue in Cases:
            CheckCircleCase(CaseValue, SourceRoot)
        assert VerifyCurves(SourceRoot) == Freeze
