from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    ObjectFields,
    NumberValue,
    PointCoords,
)
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry


# evaluated topology must agree with native mass cache after the actual corner subtraction
def CheckCutMass(
    Context: ExtrudeContext,
    Shapes: tuple[RectGeometry, RectGeometry],
    Height: float,
    Volume: float,
    AreaValue: float,
) -> None:
    Stock, ToolCut = Shapes
    MainArea = Stock.Width * Stock.Depth
    CutArea = MainArea - Volume / Height
    Remaining = MainArea - CutArea
    CornerX = (
        max(Stock.BasePoint[0], ToolCut.BasePoint[0])
        + min(Stock.BasePoint[0] + Stock.Width, ToolCut.BasePoint[0] + ToolCut.Width)
    ) / 2
    CornerY = (
        max(Stock.BasePoint[1], ToolCut.BasePoint[1])
        + min(Stock.BasePoint[1] + Stock.Depth, ToolCut.BasePoint[1] + ToolCut.Depth)
    ) / 2
    CenterX = (
        (Stock.BasePoint[0] + Stock.Width / 2) * MainArea - CornerX * CutArea
    ) / Remaining
    CenterY = (
        (Stock.BasePoint[1] + Stock.Depth / 2) * MainArea - CornerY * CutArea
    ) / Remaining
    Cache = ObjectFields(Context.BodyNode.Fields["cache"])
    SameNumbers(
        (NumberValue(Cache["volume"]) * 1000, NumberValue(Cache["area"]) * 100),
        (Volume, AreaValue),
    )
    SameNumbers(PointCoords(Cache["cog"]), (CenterX / 10, CenterY / 10, Height / 20))
