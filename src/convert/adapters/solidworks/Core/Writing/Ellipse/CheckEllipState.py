from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import ReadMeasNum


# an admitted state must measure the actual single solid on the canonical support with its live depth
def CheckEllipState(StateValue: dict[str, object]) -> tuple[float, ...]:
    Center = StateValue.get("com_m")
    if (
        type(Center) is not list
        or len(CastValue(list[object], Center)) != 3
        or any(
            type(Coord) is not float or not IsFinite(Coord)
            for Coord in CastValue(list[object], Center)
        )
        or StateValue.get("solid_count") != 1
        or StateValue.get("faces") != 3
        or StateValue.get("support") != "Front Plane"
        or StateValue.get("driver") != "D1"
        or StateValue.get("driver_state") != 2
        or StateValue.get("tree_rows") != 25
        or StateValue.get("readonly") is not False
    ):
        raise ValueError(
            "ellipse measurement lacks the owned native history and solid observations"
        )
    return (
        ReadMeasNum(StateValue.get("depth_m")),
        ReadMeasNum(StateValue.get("volume_m3")),
        ReadMeasNum(StateValue.get("area_m2")),
        *CastValue(list[float], Center),
    )
