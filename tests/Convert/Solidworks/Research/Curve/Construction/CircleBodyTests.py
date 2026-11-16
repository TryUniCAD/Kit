from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.CircleBodyInput import (
    MakeCircleBody,
)
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# isolated circle boss processes preserve complete generated native streams for independent body acceptance
def TestCircleBody() -> None:
    for NameValue, CenterValue, RadiusValue, DepthValue, ModeValue, TextPoint in (
        (
            "CircleRadiusBoss",
            [-0.004913, 0.006281],
            0.007639,
            0.012173,
            "radius",
            [0.018083, 0.025367, 0.0],
        ),
        (
            "CircleDiameterBoss",
            [0.006787, -0.003953],
            0.011147,
            0.016391,
            "diameter",
            [0.032179, 0.022501, 0.0],
        ),
    ):
        Request = MakeCircleBody(
            CenterValue, RadiusValue, DepthValue, NameValue, ModeValue, TextPoint
        )
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
        assert "moExtrusion_c" in CastValue(list[str], Report["features"])
        assert Report["configuration_progress"] is True
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["vendor_acceptance"] == "unverified"
