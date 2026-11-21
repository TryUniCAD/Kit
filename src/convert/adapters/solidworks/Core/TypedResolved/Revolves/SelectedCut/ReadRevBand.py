from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevCutBand import (
    RevCutBand,
)


# the two vertical profile lines identify the actual cylindrical walls irrespective of array order
def ReadRevBand(OwnerValue: RevolveOwner) -> RevCutBand:
    LoopValue = OwnerValue.ProfileGraph.LoopValue
    Points = LoopValue.PointsValue
    XValues = tuple(sorted({Point.PositionValue[0] for Point in Points.values()}))
    YValues = tuple(sorted({Point.PositionValue[1] for Point in Points.values()}))
    WallMarks = {
        Points[LineValue.StartValue].PositionValue[0]: LineValue.PermanentId
        for LineValue in LoopValue.LinesValue
        if Points[LineValue.StartValue].PositionValue[0]
        == Points[LineValue.EndValue].PositionValue[0]
    }
    if len(XValues) != 2 or len(YValues) != 2 or WallMarks.keys() != set(XValues):
        raise ValueError("selected revolve cut requires actual rectangular wall owners")
    Marks = frozenset(LineValue.PermanentId for LineValue in LoopValue.LinesValue)
    if len(Marks) != 4 or min(Marks) <= 0:
        raise ValueError("selected revolve cut requires four distinct contour marks")
    LowerX, Right = XValues
    Bottom, UpperY = YValues
    return RevCutBand(
        (LowerX, Right), (Bottom, UpperY), (WallMarks[LowerX], WallMarks[Right]), Marks
    )
