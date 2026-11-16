from __future__ import annotations

from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.Construction.CircleBodyInput import (
    MakeCircleBody,
)
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# independent principal plane requests exercise native circle frames through fresh complete archive processes
def TestPlaneCircle() -> None:
    for (
        NameValue,
        PlaneAxis,
        CenterValue,
        RadiusValue,
        DepthValue,
        ModeValue,
        TextPoint,
    ) in (
        (
            "RadiusRightBoss",
            "x",
            [0.003271, -0.005819],
            0.008123,
            0.014287,
            "radius",
            [0.0, 0.016231, -0.024317],
        ),
        (
            "DiameterTopBoss",
            "y",
            [-0.006139, 0.004723],
            0.010091,
            0.009827,
            "diameter",
            [0.021743, 0.0, -0.027191],
        ),
    ):
        Request = MakeCircleBody(
            CenterValue, RadiusValue, DepthValue, NameValue, ModeValue, TextPoint
        )
        Document = CastValue(dict[str, object], Request["document"])
        Document["plane_axis"] = PlaneAxis
        Report = RunFreshPart(Request)
        SavePartOutput(NameValue, Request, Report)
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert len(Streams) == 8
        assert all(
            StreamRow["passed"] and StreamRow["tail"] == 0
            for StreamRow in Streams.values()
        )
        assert Report["center_fixed"] is True and Report["has_extrusion"] is True
        assert Report["points"] == 2 and Report["arcs"] == 1 and Report["lines"] == 0
        assert Report["depth"] == DepthValue
        assert Report["configuration_progress"] is True
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["vendor_acceptance"] == "unverified"
