from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)


# sparse native point slots require walking the actual ordered contour lines
def MakeRevMeridian(OwnerValue: RevolveOwner) -> tuple[tuple[float, float], ...]:
    ProfileValue = OwnerValue.ProfileGraph
    LoopValue = ProfileValue.LoopValue
    AxisValue = ProfileValue.AxisValue
    LocalStart = ProfileValue.AxisPoints[AxisValue.StartValue].PositionValue
    LocalEnd = ProfileValue.AxisPoints[AxisValue.EndValue].PositionValue
    if LocalStart[0] != LocalEnd[0]:
        raise ValueError("cache free revolve requires its vertical sketch axis")
    OrderedValues = tuple(LoopValue.LinesValue[Index] for Index in LoopValue.OrderValue)
    InitialIndex = CurrentIndex = OrderedValues[0].StartValue
    HeightSign = -1.0 if OwnerValue.IsReverse else 1.0
    Meridian: list[tuple[float, float]] = []
    for LineValue in OrderedValues:
        PointValue = LoopValue.PointsValue[CurrentIndex].PositionValue
        Meridian.append(
            (
                PointValue[0] - LocalStart[0],
                HeightSign * (PointValue[1] - LocalStart[1]),
            )
        )
        if CurrentIndex == LineValue.StartValue:
            CurrentIndex = LineValue.EndValue
        elif CurrentIndex == LineValue.EndValue:
            CurrentIndex = LineValue.StartValue
        else:
            raise ValueError("cache free revolve contour lines do not share endpoints")
    if CurrentIndex != InitialIndex:
        raise ValueError("cache free revolve contour does not close")
    return tuple(Meridian)
