from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.CircleInput import (
    MakeCircleInput,
)
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# independent arc processes preserve signed curve geometry for complete archives and later native measurement
def TestOpenArcs() -> None:
    for NameValue, PlaneValue, CenterValue, RadiusValue, StartValue, SweepValue in (
        ("ArcPositiveSketch", "z", [-0.004731, 0.006193], 0.007137, 0.341, 1.137),
        ("ArcNegativeSketch", "y", [0.008917, -0.005381], 0.010423, -1.013, -4.319),
    ):
        Request = MakeCircleInput(CenterValue, RadiusValue, NameValue, PlaneValue)
        Document = CastValue(dict[str, object], Request["document"])
        Document.update(
            profile_kind="arc",
            start_angle_rad=StartValue,
            sweep_angle_rad=SweepValue,
        )
        Report = RunFreshPart(Request)
        SavePartOutput(NameValue, Request, Report)
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert len(Streams) == 8
        assert all(
            StreamRow["passed"] and StreamRow["tail"] == 0
            for StreamRow in Streams.values()
        )
        assert Report["points"] == 3 and Report["arcs"] == 1 and Report["lines"] == 0
        assert Report["has_extrusion"] is False and Report["radial"] is None
        assert Report["center_fixed"] is False
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["configuration_progress"] is True
        assert Report["vendor_acceptance"] == "unverified"
