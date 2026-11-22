from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckHandles import (
    CheckHandles,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineIncidence import (
    LineIncidence,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LinePoint import LinePoint
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment


# exact degree and handle joins must establish one closed ring before public loop identities are emitted
def LineOrder(
    PointsValue: tuple[LinePoint, ...],
    LinesValue: tuple[LineSegment, ...],
    *,
    LineBase: int = 0,
) -> tuple[int, ...]:
    Incident = LineIncidence(PointsValue, LinesValue)
    CheckHandles(PointsValue, Incident, LineBase=LineBase)
    OrderValue = [0]
    SeenValues = {0}
    StartValue, CurrentValue = LinesValue[0].StartValue, LinesValue[0].EndValue
    while CurrentValue != StartValue:
        NextValues = Incident[CurrentValue].difference(OrderValue[-1:])
        if len(NextValues) != 1:
            raise ValueError("typed line ring traversal is ambiguous")
        NextValue = next(iter(NextValues))
        if NextValue in SeenValues:
            raise ValueError("typed line ring traversal repeats an edge")
        OrderValue.append(NextValue)
        SeenValues.add(NextValue)
        LineValue = LinesValue[NextValue]
        CurrentValue = (
            LineValue.EndValue
            if LineValue.StartValue == CurrentValue
            else LineValue.StartValue
        )
    if len(OrderValue) != len(PointsValue):
        raise ValueError("typed line ring contains disconnected loops")
    return tuple(OrderValue)
