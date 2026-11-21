from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.CircleInput import (
    MakeCircleInput,
)
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# independent process inputs expose fixed topology assumptions and preserve generated files for native inspection
def TestCircleSets() -> None:
    PreviousSizes = None
    for NameValue, PlaneValue, CircleValues in (
        (
            "DualCircleSketch",
            "z",
            [([-0.025701, -0.022913], 0.003827), ([0.024473, -0.021139], 0.005617)],
        ),
        (
            "FourCircleSketch",
            "z",
            [
                ([-0.025701, -0.022913], 0.003827),
                ([0.024473, -0.021139], 0.005617),
                ([0.023129, 0.028339], 0.006421),
                ([-0.027437, 0.026783], 0.004739),
            ],
        ),
    ):
        Request = MakeCircleInput([0.0, 0.0], 0.001, NameValue, PlaneValue)
        Document = CastValue(dict[str, object], Request["document"])
        del Document["center_m"]
        del Document["radius_m"]
        Document.update(
            profile_kind="circle_set",
            circles_m=[
                {"center_m": CenterValue, "radius_m": RadiusValue}
                for CenterValue, RadiusValue in CircleValues
            ],
        )
        Report = RunFreshPart(Request)
        SavePartOutput(NameValue, Request, Report)
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert len(Streams) == 8
        assert all(
            StreamRow["passed"] and StreamRow["tail"] == 0
            for StreamRow in Streams.values()
        )
        assert Report["points"] == 2 * len(CircleValues)
        assert Report["arcs"] == len(CircleValues) and Report["lines"] == 0
        assert Report["has_extrusion"] is False and Report["radial"] is None
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["configuration_progress"] is True
        assert Report["vendor_acceptance"] == "unverified"
        Sizes = CastValue(dict[str, int], Report["sizes"])
        if PreviousSizes is not None:
            assert Sizes["Contents/Config-0"] == PreviousSizes["Contents/Config-0"]
            assert (
                Sizes["Contents/Config-0-ResolvedFeatures"]
                > PreviousSizes["Contents/Config-0-ResolvedFeatures"]
            )
        PreviousSizes = Sizes
