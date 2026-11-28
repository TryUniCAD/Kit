from __future__ import annotations

from math import isclose as IsClose
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.FreshPartTests import AssertPart


# redecoded relations and displays show how each driving dimension is connected
def AssertRectangle(
    Report: dict[str, object],
    DepthValue: float,
    ExpectedSizes: list[float],
    TextAnchors: list[list[float]],
    RouteCenterline: bool,
    *,
    StreamCount: int = 8,
) -> None:
    AssertPart(Report, 4, DepthValue, StreamCount)
    Rectangle = CastValue(dict[str, object], Report["rectangle"])
    Values = CastValue(list[dict[str, object]], Rectangle["values"])
    assert Rectangle["logical_types"] == [4, 5, 4, 5]
    assert Rectangle["logical_line_slots"] == [0, 1, 2, 3]
    assert Rectangle["point_references"] == [1, 2, 1, 0]
    assert Rectangle["line_references"] == [1, 1, 1, 1]
    assert Rectangle["next_display_id"] == 12
    assert [Value["name"] for Value in Values] == ["D1", "D2"]
    assert [Value["endpoint_slots"] for Value in Values] == [[0, 1], [1, 2]]
    assert [Value["display_handle_slot"] for Value in Values] == [0, 1]
    assert [Value["display_id"] for Value in Values] == [10, 11]
    assert len({Value["id"] for Value in Values}) == 2
    assert Rectangle["keywords"] == {
        CastValue(str, Value["name"]): CastValue(float, Value["value_m"]) / 0.001
        for Value in Values
    }
    for Value, Length, Anchor in zip(Values, ExpectedSizes, TextAnchors, strict=True):
        assert Value["value_class"] == "sgPntPntDist"
        assert Value["parameter_class"] == "moLengthParameter_c"
        assert Value["display_class"] == "moDisplayDistanceDim_c"
        assert Value["display_handle_class"] == "moSkDimHandleValG2_c"
        assert Value["display_owns_sketch"] is True
        assert Value["route_centerline"] is RouteCenterline
        assert Value["parameter_id"] == -1 and Value["driven"] == 0
        assert Value["display_text_m"] == [*Anchor, 0.0]
        assert IsClose(CastValue(float, Value["value_m"]), Length, abs_tol=1e-15)
        assert Value["display_value_m"] == Value["value_m"]
