from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.CircleInput import (
    MakeCircleInput,
)


# authored radial intent supplies presentation and driving value without any native source document
def MakeRadialInput(
    CenterValue: list[float],
    RadiusValue: float,
    NameValue: str,
    ModeValue: str,
    TextPoint: list[float],
) -> dict[str, object]:
    Request = MakeCircleInput(CenterValue, RadiusValue, NameValue, "z")
    Document = CastValue(dict[str, object], Request["document"])
    Document["circle_dimension"] = {"mode": ModeValue, "text_point_m": TextPoint}
    return Request
