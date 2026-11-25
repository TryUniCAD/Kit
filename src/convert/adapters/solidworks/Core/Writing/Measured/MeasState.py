from typing import cast as CastValue
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import (
    ReadMeasNum,
    ReadMeasReal,
)


# recorded frame and solid measurements must be present for every accepted observation
def MeasState(
    StateValue: dict[str, object],
) -> tuple[int, tuple[float, ...]]:
    TreeCount = StateValue.get("rows")
    Center = StateValue.get("centre_of_mass_m")
    if (
        type(StateValue.get("bodies")) is not int
        or StateValue["bodies"] != 1
        or type(StateValue.get("warnings")) is not int
        or StateValue["warnings"] != 0
        or type(TreeCount) is not int
        or TreeCount < 1
        or type(Center) is not list
        or len(CastValue(list[object], Center)) != 3
    ):
        raise ValueError(
            "native measurement has an incomplete or unclean solid observation"
        )
    return TreeCount, (
        ReadMeasNum(StateValue.get("depth_m")),
        ReadMeasNum(StateValue.get("volume_m3")),
        ReadMeasNum(StateValue.get("area_m2")),
        *(ReadMeasReal(Coord) for Coord in CastValue(list[object], Center)),
    )
