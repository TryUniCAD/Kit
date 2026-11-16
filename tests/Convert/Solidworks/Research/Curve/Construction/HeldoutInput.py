from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.CircleBodyInput import (
    MakeCircleBody,
)


# heldout requests must preserve independent source parameters without consuming saved native payloads
def MakeHeldBody(CaseValue: dict[str, object]) -> dict[str, object]:
    Profile = CastValue(dict[str, object], CaseValue["profile"])
    Center = [Value / 1000 for Value in CastValue(list[float], Profile["center_mm"])]
    Radius = CastValue(float, Profile["radius_mm"]) / 1000
    Depth = CastValue(float, CaseValue["depth_mm"]) / 1000
    PlaneAxis = {"front": "z", "right": "x", "top": "y"}[
        CastValue(str, CaseValue["plane"])
    ]
    LocalText = [Center[0] + 1.7 * Radius, Center[1] + 1.3 * Radius]
    TextPoint = {
        "z": [LocalText[0], LocalText[1], 0.0],
        "x": [0.0, LocalText[1], -LocalText[0]],
        "y": [LocalText[0], 0.0, -LocalText[1]],
    }[PlaneAxis]
    Request = MakeCircleBody(
        Center,
        Radius,
        Depth,
        CastValue(str, CaseValue["name"]),
        CastValue(str, CaseValue["dimension_kind"]),
        TextPoint,
    )
    Document = CastValue(dict[str, object], Request["document"])
    Document.update(
        feature_kind="extrusion",
        end_condition=CaseValue["end_condition"],
        reverse_direction=CaseValue["reverse"],
        plane_axis=PlaneAxis,
        sketch_name="CurveSketch",
        extrusion_name="CurveBoss",
        origin_name="Origin",
    )
    if CaseValue["end_condition"] == "two_directions":
        Document["reverse_depth_m"] = (
            CastValue(float, CaseValue["reverse_depth_mm"]) / 1000
        )
    return Request
