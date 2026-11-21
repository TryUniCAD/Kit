from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.DrivingInput import (
    MakeRadialInput,
)
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# generated fixed center requests exercise complete native constraint ownership through isolated processes
def TestFixedCenter() -> None:
    for NameValue, CenterValue, RadiusValue, ModeValue, TextPoint in (
        (
            "FixedRadius",
            [-0.005983, 0.002179],
            0.006257,
            "radius",
            [0.013751, 0.015529, 0.0],
        ),
        (
            "FixedDiameter",
            [0.008939, -0.004183],
            0.010343,
            "diameter",
            [0.028617, 0.018997, 0.0],
        ),
    ):
        Request = MakeRadialInput(
            CenterValue, RadiusValue, NameValue, ModeValue, TextPoint, True
        )
        Report = RunFreshPart(Request)
        SavePartOutput(NameValue, Request, Report)
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert len(Streams) == 8
        assert all(
            StreamRow["passed"] and StreamRow["tail"] == 0
            for StreamRow in Streams.values()
        )
        assert Report["center_fixed"] is True
        assert Report["points"] == 2 and Report["arcs"] == 1 and Report["lines"] == 0
        assert Report["has_extrusion"] is False
        assert Report["configuration_progress"] is True
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["vendor_acceptance"] == "unverified"
