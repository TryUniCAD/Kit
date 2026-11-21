from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.DrivingInput import (
    MakeRadialInput,
)
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.PartArtifacts import SavePartOutput


# independent processes exercise native radial objects and preserve outputs for controlled vendor inspection
def TestRadialBuild() -> None:
    for NameValue, CenterValue, RadiusValue, ModeValue, TextPoint, NativeType in (
        (
            "DrivingRadius",
            [-0.002983, 0.004129],
            0.005347,
            "radius",
            [0.013729, 0.016811, 0.0],
            3,
        ),
        (
            "DrivingDiameter",
            [0.007541, -0.006389],
            0.008779,
            "diameter",
            [0.025923, 0.014357, 0.0],
            15,
        ),
    ):
        Request = MakeRadialInput(
            CenterValue, RadiusValue, NameValue, ModeValue, TextPoint
        )
        Report = RunFreshPart(Request)
        SavePartOutput(NameValue, Request, Report)
        Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
        assert len(Streams) == 8
        assert all(
            StreamRow["passed"] and StreamRow["tail"] == 0
            for StreamRow in Streams.values()
        )
        RadialValue = CastValue(dict[str, object], Report["radial"])
        assert RadialValue["type"] == NativeType and RadialValue["name"] == "D1"
        assert RadialValue["parameter_id"] == -1 and RadialValue["reference_count"] == 0
        assert CastValue(int, RadialValue["dimension_id"]) < CastValue(
            int, Report["next_id"]
        )
        assert RadialValue["handle_class"] == "moSkDimHandleRadial_c"
        assert RadialValue["display_class"] == "moDisplayRadialDim_c"
        assert Report["points"] == 2 and Report["lines"] == 0 and Report["arcs"] == 1
        assert (
            Report["has_extrusion"] is False
            and Report["configuration_progress"] is True
        )
        assert Report["denied_reads"] == [] and Report["module_reads"]
        assert Report["vendor_acceptance"] == "unverified"
