from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.CircleInput import (
    MakeCircleInput,
)
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# separate guarded processes bind generated circle topology to strict complete archive roundtrips
def TestCircleSketches() -> None:
    for NameValue, CenterValue, RadiusValue, PlaneValue in (
        ("CircleSketchOne", [-0.004237, 0.003551], 0.006713, "z"),
        ("CircleSketchTwo", [0.009263, -0.012217], 0.015137, "x"),
    ):
        Request = MakeCircleInput(CenterValue, RadiusValue, NameValue, PlaneValue)
        Report = RunFreshPart(Request)
        SavePartOutput(NameValue, Request, Report)
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert len(Streams) == 8
        assert all(Row["passed"] and Row["tail"] == 0 for Row in Streams.values())
        assert Report["points"] == 2 and Report["lines"] == 0 and Report["arcs"] == 1
        assert Report["depth"] is None and Report["has_extrusion"] is False
        assert "moProfileFeature_c" in CastValue(list[str], Report["features"])
        assert "moExtrusion_c" not in CastValue(list[str], Report["features"])
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["configuration_progress"] is True
        assert Report["vendor_acceptance"] == "unverified"
