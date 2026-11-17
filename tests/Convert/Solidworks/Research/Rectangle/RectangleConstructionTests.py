from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.Rectangle.AssertRectangle import AssertRectangle
from tests.Convert.Solidworks.Research.Rectangle.RectangleInput import (
    MakeRectangleInput,
)


# separate guarded processes establish changed graph sizes and changing values from fresh inputs
def TestRectangleConstruction() -> None:
    FirstText = [[-0.009, -0.014], [0.034, 0.003]]
    SecondText = [[0.031, -0.021], [0.047, -0.005]]
    First = MakeRectangleInput(
        "GeneratedWidthHeightCentered",
        [[-0.027, -0.009], [0.027, -0.009], [0.027, 0.009], [-0.027, 0.009]],
        0.013,
        FirstText,
        False,
    )
    Second = MakeRectangleInput(
        "GeneratedWidthHeightTranslated",
        [[0.005, -0.013], [0.042, -0.013], [0.042, 0.016], [0.005, 0.016]],
        0.0082,
        SecondText,
        True,
    )
    FirstReport, SecondReport = RunFreshPart(First), RunFreshPart(Second)
    AssertRectangle(FirstReport, 0.013, [0.054, 0.018], FirstText, False)
    AssertRectangle(SecondReport, 0.0082, [0.037, 0.029], SecondText, True)
    Document = dict(CastValue(dict[str, object], First["document"]))
    Document.pop("rectangle_dimensions")
    Baseline = RunFreshPart({**First, "document": Document})
    assert Baseline.get("rectangle") is None
    assert (
        Baseline["map_count"] == FirstReport["map_count"] == SecondReport["map_count"]
    )
    assert (
        CastValue(int, Baseline["next_id"]) + 2
        == FirstReport["next_id"]
        == SecondReport["next_id"]
    )
    Resolved = "Contents/Config-0-ResolvedFeatures"
    IndexedBytes = CastValue(dict[str, int], FirstReport["sizes"])[Resolved]
    assert IndexedBytes > CastValue(dict[str, int], Baseline["sizes"])[Resolved]
