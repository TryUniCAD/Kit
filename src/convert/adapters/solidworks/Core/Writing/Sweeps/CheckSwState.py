from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import ReadMeasNum


# each state reports the actual two editable drivers and measured mass of one native solid
def CheckSwState(State: dict[str, object]) -> tuple[float, ...]:
    Center = State.get("com_m")
    if (
        type(Center) is not list
        or len(CastValue(list[object], Center)) != 3
        or any(
            type(Coord) is not float or not IsFinite(Coord)
            for Coord in CastValue(list[object], Center)
        )
        or State.get("solid_count") != 1
        or State.get("faces") != 3
        or State.get("tree_rows") != 26
        or State.get("drivers")
        != [["D1", "SweepSection", 6, 2, False], ["D1", "SweepPath", 5, 2, False]]
    ):
        raise ValueError(
            "sweep measurement lacks the two owned driving dimensions and solid"
        )
    return (
        ReadMeasNum(State.get("section_diameter_m")),
        ReadMeasNum(State.get("path_radius_m")),
        ReadMeasNum(State.get("volume_m3")),
        ReadMeasNum(State.get("area_m2")),
        ReadMeasNum(State.get("mass_kg")),
        *CastValue(list[float], Center),
    )
