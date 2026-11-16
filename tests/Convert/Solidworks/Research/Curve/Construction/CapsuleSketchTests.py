from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.CircleInput import (
    MakeCircleInput,
)
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# guarded capsule processes exercise shared endpoint identities across native line and arc arrays
def TestCapsule() -> None:
    for NameValue, PlaneValue, CenterValue, RadiusValue, LengthValue, AngleValue in (
        ("CapsuleSketchSmall", "z", [-0.004183, 0.007291], 0.004637, 0.019373, 0.417),
        (
            "CapsuleSketchRotated",
            "x",
            [0.009217, -0.005713],
            0.007643,
            0.028619,
            -0.731,
        ),
    ):
        Request = MakeCircleInput(CenterValue, RadiusValue, NameValue, PlaneValue)
        Document = CastValue(dict[str, object], Request["document"])
        Document.update(
            profile_kind="capsule",
            straight_length_m=LengthValue,
            rotation_angle_rad=AngleValue,
        )
        Report = RunFreshPart(Request)
        SavePartOutput(NameValue, Request, Report)
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert len(Streams) == 8
        assert all(
            StreamRow["passed"] and StreamRow["tail"] == 0
            for StreamRow in Streams.values()
        )
        assert Report["points"] == 6 and Report["arcs"] == Report["lines"] == 2
        assert Report["has_extrusion"] is False and Report["radial"] is None
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["configuration_progress"] is True
        assert Report["vendor_acceptance"] == "unverified"
