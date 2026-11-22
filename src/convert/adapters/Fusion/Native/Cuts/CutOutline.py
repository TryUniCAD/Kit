from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# clipping the authored rectangles derives a simple corner boundary without fixture coordinates
def CutOutline(Stock: RectGeometry, ToolCut: RectGeometry) -> tuple[PlaneVector, ...]:
    StartX, StartY = Stock.BasePoint[:2]
    FinishX, FinishY = StartX + Stock.Width, StartY + Stock.Depth
    LowerX, LowerY = max(StartX, ToolCut.BasePoint[0]), max(
        StartY, ToolCut.BasePoint[1]
    )
    HighX, HighY = min(FinishX, ToolCut.BasePoint[0] + ToolCut.Width), min(
        FinishY, ToolCut.BasePoint[1] + ToolCut.Depth
    )
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
