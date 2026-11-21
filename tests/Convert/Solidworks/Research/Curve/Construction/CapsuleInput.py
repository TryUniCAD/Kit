from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Curve.Construction.CircleInput import (
    MakeCircleInput,
)


# shared neutral capsule requests keep sketch and body processes independent from native control files
def MakeCapsule(
    CenterValue: list[float],
    RadiusValue: float,
    LengthValue: float,
    AngleValue: float,
    NameValue: str,
    PlaneValue: str,
) -> dict[str, object]:
    Request = MakeCircleInput(CenterValue, RadiusValue, NameValue, PlaneValue)
    Document = CastValue(dict[str, object], Request["document"])
    Document.update(
        profile_kind="capsule",
        straight_length_m=LengthValue,
        rotation_angle_rad=AngleValue,
    )
    return Request
