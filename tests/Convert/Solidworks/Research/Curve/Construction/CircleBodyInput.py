from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.DrivingInput import (
    MakeRadialInput,
)


# explicit body inputs reuse the measured constrained circle graph and existing blind feature model
def MakeCircleBody(
    CenterValue: list[float],
    RadiusValue: float,
    DepthValue: float,
    NameValue: str,
    ModeValue: str,
    TextPoint: list[float],
) -> dict[str, object]:
    Request = MakeRadialInput(
        CenterValue, RadiusValue, NameValue, ModeValue, TextPoint, True
    )
    Document = CastValue(dict[str, object], Request["document"])
    Document.update(feature_kind="blind_extrusion", depth_m=DepthValue)
    return Request
