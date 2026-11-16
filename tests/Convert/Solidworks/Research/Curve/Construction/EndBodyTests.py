from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.CircleBodyInput import (
    MakeCircleBody,
)
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# independent native candidates must exercise distinct termination and direction semantics through complete guarded processes
def TestEndBodies() -> None:
    for (
        NameValue,
        CenterValue,
        RadiusValue,
        DepthValue,
        ModeValue,
        EndValue,
        ReverseValue,
        PlaneAxis,
        SecondDepth,
        TextPoint,
    ) in (
        (
            "ReverseCircleBoss",
            [-0.006137, 0.004729],
            0.009173,
            0.014381,
            "radius",
            "blind",
            True,
            "z",
            None,
            [0.021719, 0.027913, 0.0],
        ),
        (
            "MidPlaneCircleBoss",
            [0.008271, -0.005419],
            0.006713,
            0.021943,
            "diameter",
            "mid_plane",
            False,
            "x",
            None,
            [0.0, 0.018137, -0.029719],
        ),
        (
            "DualCircleBoss",
            [-0.004913, 0.007231],
            0.010137,
            0.017191,
            "radius",
            "two_directions",
            True,
            "y",
            0.006431,
            [0.022831, 0.0, -0.028317],
        ),
    ):
        Request = MakeCircleBody(
            CenterValue,
            RadiusValue,
            DepthValue,
            NameValue,
            ModeValue,
            TextPoint,
        )
        Document = CastValue(dict[str, object], Request["document"])
        Document.update(
            feature_kind="extrusion",
            end_condition=EndValue,
            reverse_direction=ReverseValue,
            plane_axis=PlaneAxis,
        )
        if SecondDepth is not None:
            Document["reverse_depth_m"] = SecondDepth
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
        assert Report["depth"] == DepthValue and Report["reverse_depth"] == SecondDepth
        assert Report["end_condition"] == EndValue
        assert Report["reverse_direction"] is ReverseValue
        assert Report["configuration_progress"] is True
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["vendor_acceptance"] == "unverified"
