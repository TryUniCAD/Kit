from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.Construction.HeldoutInput import (
    MakeHeldBody,
)
from tests.Convert.Solidworks.Research.Curve.Heldout.CircleFreeze import (
    VerifyCircleFreeze,
)
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# original circle heldouts must pass complete guarded emission without borrowing the other profiles
def TestCircleHoldout() -> None:
    Freeze = VerifyCircleFreeze()
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
        assert CaseValue["dimension_kind"] in ("diameter", "radial")
        Mode = "radius" if CaseValue["dimension_kind"] == "radial" else "diameter"
        NeutralCase = CaseValue | {"end_condition": "blind", "dimension_kind": Mode}
        Request = MakeHeldBody(NeutralCase)
        Report = RunFreshPart(Request)
        SavePartOutput(CastValue(str, CaseValue["name"]), Request, Report)
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert len(Streams) == 8
        assert all(
            Stream["passed"] and Stream["tail"] == 0 for Stream in Streams.values()
        )
        assert Report["center_fixed"] is True and Report["has_extrusion"] is True
        assert Report["points"] == 2 and Report["arcs"] == 1 and Report["lines"] == 0
        assert Report["end_condition"] == "blind"
        assert Report["reverse_direction"] is CaseValue["reverse"]
        assert Report["configuration_progress"] is True
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["vendor_acceptance"] == "unverified"
    assert VerifyCircleFreeze() == Freeze
