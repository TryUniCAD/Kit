from __future__ import annotations

from math import isclose as IsClose
from typing import cast as CastValue


# in parent coordinates the rigid transform moves the bounds and preserves the child radius
def CheckPlacement(
    Report: dict[str, object],
    Reference: dict[str, object],
    Origin: list[float],
    AxisX: list[float],
    AxisY: list[float],
    Center: tuple[float, ...],
    HighCorner: tuple[float, ...],
    LowCorner: tuple[float, ...],
) -> None:
    Transform = CastValue(dict[str, object], Reference["transform"])
    assert [Transform[AxisKey] for AxisKey in ("f58", "f60", "f68")] == Origin
    if AxisX == [1.0, 0.0, 0.0]:
        assert Transform["has_matrix"] == 0
    else:
        Matrix = CastValue(dict[str, float], Transform["f08"])
        assert Transform["has_matrix"] == 1
        assert [Matrix[f"m{Index}"] for Index in range(9)] == [
            *AxisX,
            *AxisY,
            0.0,
            0.0,
            1.0,
        ]
    LocalBox = CastValue(dict[str, float], Reference["local_bounds"])
    FirstBox, SecondBox = CastValue(list[dict[str, float]], Report["bounds"])
    assert FirstBox == SecondBox and FirstBox["b9"] == LocalBox["b9"]
    for Index, Value in enumerate((*Center, *HighCorner, *LowCorner)):
        assert IsClose(FirstBox[f"b{Index}"], Value, abs_tol=1e-12)
