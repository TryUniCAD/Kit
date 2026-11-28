from collections.abc import Mapping

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
    PointsValue: Mapping[int, LinePoint], LinesValue: tuple[LineSegment, ...]
) -> tuple[int, ...]:
    Incident = LineIncidence(PointsValue, LinesValue)
    CheckHandles(PointsValue, Incident)
    OrderValue = [0]
    Indices = {
        LineValue.IndexValue: Index for Index, LineValue in enumerate(LinesValue)
    }
    if len(Indices) != len(LinesValue):
        raise ValueError("typed line ring has duplicate actual line slots")
    CurrentIndex = LinesValue[0].IndexValue
    SeenValues = {CurrentIndex}
    StartValue, CurrentValue = LinesValue[0].StartValue, LinesValue[0].EndValue
    while CurrentValue != StartValue:
        NextValues = Incident[CurrentValue].difference((CurrentIndex,))
        if len(NextValues) != 1:
            raise ValueError("typed line ring traversal is ambiguous")
        NextValue = next(iter(NextValues))
        if NextValue in SeenValues:
            raise ValueError("typed line ring traversal repeats an edge")
        OrderValue.append(Indices[NextValue])
        SeenValues.add(NextValue)
        CurrentIndex = NextValue
        LineValue = LinesValue[Indices[NextValue]]
        CurrentValue = (
            LineValue.EndValue
            if LineValue.StartValue == CurrentValue
            else LineValue.StartValue
        )
    if len(OrderValue) != len(PointsValue):
        raise ValueError("typed line ring contains disconnected loops")
    return tuple(OrderValue)
