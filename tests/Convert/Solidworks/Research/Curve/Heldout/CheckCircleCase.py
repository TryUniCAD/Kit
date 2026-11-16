from __future__ import annotations

from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.HeldoutInput import (
    MakeHeldBody,
)
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.Frozen.ComparePinned import ComparePinned
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# circle regressions must retain independent measured bytes across both current and historical processes
def CheckCircleCase(CaseValue: dict[str, object], SourceRoot: FilePath) -> None:
    assert CaseValue["dimension_kind"] in ("diameter", "radial")
    ModeValue = "radius" if CaseValue["dimension_kind"] == "radial" else "diameter"
    NeutralCase = CaseValue | {"end_condition": "blind", "dimension_kind": ModeValue}
    Request = MakeHeldBody(NeutralCase)
    Report = RunFreshPart(Request)
    Report["frozen_regression"] = ComparePinned(Report, Request, SourceRoot, False)
    SavePartOutput(CastValue(str, CaseValue["name"]), Request, Report)
    Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
    assert len(Streams) == 8
    assert all(Stream["passed"] and Stream["tail"] == 0 for Stream in Streams.values())
    assert Report["center_fixed"] is True and Report["has_extrusion"] is True
    assert Report["points"] == 2 and Report["arcs"] == 1 and Report["lines"] == 0
    assert Report["end_condition"] == "blind"
    assert Report["reverse_direction"] is CaseValue["reverse"]
    assert Report["configuration_progress"] is True
    assert Report["denied_reads"] == [] and Report["module_reads"]
    assert Report["vendor_acceptance"] == "unverified"
