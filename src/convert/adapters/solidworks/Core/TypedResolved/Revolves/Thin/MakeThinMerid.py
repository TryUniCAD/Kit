from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.RevolveProfile import (
    RevolveProfile,
)


# the solid wall derives from its own radial thickness relative to the selected local axis
def MakeThinMerid(
    ProfileValue: RevolveProfile, ModeValue: str, FirstValue: float, SecondValue: float
) -> tuple[tuple[float, float], ...]:
    AxisValue = ProfileValue.AxisValue
    AxisLow = ProfileValue.AxisPoints[AxisValue.StartValue].PositionValue
    AxisHigh = ProfileValue.AxisPoints[AxisValue.EndValue].PositionValue
    (BodyValue,) = ProfileValue.LoopValue.LinesValue
    BodyLow = ProfileValue.LoopValue.PointsValue[BodyValue.StartValue].PositionValue
    BodyHigh = ProfileValue.LoopValue.PointsValue[BodyValue.EndValue].PositionValue
    RadiusValue = BodyLow[0] - AxisLow[0]
    FirstWidth, SecondWidth = FirstValue * 1000.0, SecondValue * 1000.0
    if not (
        AxisLow[0] == AxisHigh[0] < BodyLow[0] == BodyHigh[0]
        and AxisLow[1] < BodyLow[1] < BodyHigh[1] < AxisHigh[1]
        and 0.0 < FirstWidth < RadiusValue
        and 0.0 <= SecondWidth < RadiusValue
        and FirstWidth != SecondWidth
    ):
        raise ValueError("SOLIDWORKS thin wall exceeds the measured axial domain")
    Outward = FirstWidth if ModeValue in ("one_sided", "two_sided") else 0.0
    Inward = FirstWidth if ModeValue == "opposite" else SecondWidth
    if ModeValue == "midplane":
        Inward = Outward = FirstWidth / 2.0
    Inner, Outer = RadiusValue - Inward, RadiusValue + Outward
    Lower, Upper = BodyLow[1] - AxisLow[1], BodyHigh[1] - AxisLow[1]
    return ((Inner, Lower), (Outer, Lower), (Outer, Upper), (Inner, Upper))
