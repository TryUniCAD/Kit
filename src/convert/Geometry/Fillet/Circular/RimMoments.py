from math import isfinite as IsFinite, pi as CirclePi


# exact radial slice integrals preserve every mass component of a constant top circular fillet
def RimMoments(
    Radius: float, Height: float, Fillet: float
) -> tuple[float, float, float, float, float]:
    try:
        if any(
            type(Value) not in (int, float) or not IsFinite(Value)
            for Value in (Radius, Height, Fillet)
        ) or not 0 < Fillet < min(Radius, Height):
            raise ValueError("Circular rim requires finite positive bounded dimensions")
        MajorRadius = Radius - Fillet
        LowerHeight = Height - Fillet
        if MajorRadius == Radius or LowerHeight == Height:
            raise ValueError("Circular rim disappears at coordinate precision")
        FlatMoment = (
            MajorRadius**2 * Fillet
            + CirclePi * MajorRadius * Fillet**2 / 2
            + 2 * Fillet**3 / 3
        )
        FirstMoment = (
            MajorRadius**2 * Fillet**2 / 2
            + 2 * MajorRadius * Fillet**3 / 3
            + Fillet**4 / 4
        )
        AxialMoment = (
            MajorRadius**2 * Fillet**3 / 3
            + CirclePi * MajorRadius * Fillet**4 / 8
            + 2 * Fillet**5 / 15
        )
        FourthMoment = (
            MajorRadius**4 * Fillet
            + CirclePi * MajorRadius**3 * Fillet**2
            + 4 * MajorRadius**2 * Fillet**3
            + 3 * CirclePi * MajorRadius * Fillet**4 / 4
            + 8 * Fillet**5 / 15
        )
        Volume = CirclePi * (Radius**2 * LowerHeight + FlatMoment)
        Center = (
            CirclePi
            * (Radius**2 * LowerHeight**2 / 2 + LowerHeight * FlatMoment + FirstMoment)
            / Volume
        )
        AreaValue = CirclePi * (
            Radius**2
            + 2 * Radius * LowerHeight
            + MajorRadius**2
            + CirclePi * MajorRadius * Fillet
            + 2 * Fillet**2
        )
        Radial = CirclePi * (Radius**4 * LowerHeight + FourthMoment) / 4
        Axial = CirclePi * (
            Radius**2 * LowerHeight**3 / 3
            + LowerHeight**2 * FlatMoment
            + 2 * LowerHeight * FirstMoment
            + AxialMoment
        )
    except (OverflowError, ZeroDivisionError) as ErrorValue:
        raise ValueError("Circular rim measures exceed finite geometry") from ErrorValue
    if not all(
        IsFinite(Value) and Value > 0
        for Value in (Volume, AreaValue, Center, Radial, Axial)
    ):
        raise ValueError("Circular rim requires finite positive measures")
    return Volume, AreaValue, Center, Radial, Axial
