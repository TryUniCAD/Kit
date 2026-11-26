from fractions import Fraction

from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepEdge import (
    SweepEdge,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepEvent import (
    SweepEvent,
)


# exact abscissa grouping preserves all starts ends and vertical edges without changing vertex order
def MakeSweepEvents(
    PointsValue: tuple[tuple[Fraction, Fraction], ...],
) -> dict[Fraction, SweepEvent]:
    EventsValue: dict[Fraction, SweepEvent] = {}
    for IndexValue, PointValue in enumerate(PointsValue):
        StartValue, EndValue = sorted(
            (PointValue, PointsValue[(IndexValue + 1) % len(PointsValue)])
        )
        IsVertical = StartValue[0] == EndValue[0]
        EdgeValue = SweepEdge(
            IndexValue,
            StartValue,
            EndValue,
            (
                None
                if IsVertical
                else (EndValue[1] - StartValue[1]) / (EndValue[0] - StartValue[0])
            ),
        )
        StartEvent = EventsValue.setdefault(StartValue[0], SweepEvent())
        if IsVertical:
            StartEvent.VerticalValue.append(EdgeValue)
        else:
            StartEvent.StartsValue.append(EdgeValue)
            EventsValue.setdefault(EndValue[0], SweepEvent()).EndsValue.append(
                EdgeValue
            )
    return EventsValue
