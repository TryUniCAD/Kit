from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.CapsuleInput import (
    MakeCapsule,
)
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# complete capsule boss processes retain independent native artifacts for later mass and depth edit measurements
def TestCapsuleBody() -> None:
    for (
        NameValue,
        PlaneValue,
        CenterValue,
        RadiusValue,
        LengthValue,
        AngleValue,
        DepthValue,
    ) in (
        (
            "CapsuleBossOne",
            "z",
            [-0.003817, 0.005963],
            0.005127,
            0.022619,
            0.289,
            0.011827,
        ),
        (
            "CapsuleBossTwo",
            "y",
            [0.007193, -0.006347],
            0.008239,
            0.031733,
            -0.617,
            0.017311,
        ),
    ):
        Request = MakeCapsule(
            CenterValue, RadiusValue, LengthValue, AngleValue, NameValue, PlaneValue
        )
        Document = CastValue(dict[str, object], Request["document"])
        Document.update(feature_kind="blind_extrusion", depth_m=DepthValue)
        Report = RunFreshPart(Request)
        SavePartOutput(NameValue, Request, Report)
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert len(Streams) == 8
        assert all(
            StreamRow["passed"] and StreamRow["tail"] == 0
            for StreamRow in Streams.values()
        )
        assert Report["points"] == 6 and Report["lines"] == Report["arcs"] == 2
        assert Report["has_extrusion"] is True and Report["depth"] == DepthValue
        assert Report["radial"] is None and Report["configuration_progress"] is True
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["vendor_acceptance"] == "unverified"
