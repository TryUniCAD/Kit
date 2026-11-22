from convert.adapters.Fusion.Native.Cuts.ClipCornerAxis import ClipCornerAxis
from convert.adapters.Fusion.Native.Rectangle.ReadRectBounds import ReadRectBounds
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# clipping the authored rectangles derives a simple corner boundary without fixture coordinates
def CutOutline(Stock: RectGeometry, ToolCut: RectGeometry) -> tuple[PlaneVector, ...]:
    StartX, FinishX, StartY, FinishY = ReadRectBounds(Stock.Lines, Scoped=True)
    ToolLowerX, ToolUpperX, ToolLowerY, ToolUpperY = ReadRectBounds(
        ToolCut.Lines, Scoped=True
    )
    LowerX, HighX = ClipCornerAxis(StartX, FinishX, ToolLowerX, ToolUpperX)
    LowerY, HighY = ClipCornerAxis(StartY, FinishY, ToolLowerY, ToolUpperY)
    if (
        not (0 < HighX - LowerX < Stock.Width and 0 < HighY - LowerY < Stock.Depth)
        or ((LowerX == StartX) == (HighX == FinishX))
        or ((LowerY == StartY) == (HighY == FinishY))
    ):
        raise ValueError("Native cut profile does not remove one bounded stock corner")
    FlipX, FlipY = LowerX == StartX, LowerY == StartY
    CornerX, CornerY = FinishX - (HighX - LowerX), FinishY - (HighY - LowerY)
    Points = (
        (StartX, StartY),
        (FinishX, StartY),
        (FinishX, CornerY),
        (CornerX, CornerY),
        (CornerX, FinishY),
        (StartX, FinishY),
    )
    Result = tuple(
        PlaneVector(
            StartX + FinishX - First if FlipX else First,
            StartY + FinishY - Second if FlipY else Second,
        )
        for First, Second in Points
    )
    return tuple(reversed(Result)) if FlipX != FlipY else Result
