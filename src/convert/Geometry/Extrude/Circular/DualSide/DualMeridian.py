from math import isfinite as IsFinite, pi as CirclePi, tan as Tangent


# independent side drafts require a bounded radial graph without assuming convexity
def DualMeridian(
    Radius: float,
    FirstMm: float,
    SecondMm: float,
    FirstTaper: float,
    SecondTaper: float,
) -> tuple[tuple[float, float], ...]:
    Controls = (Radius, FirstMm, SecondMm, FirstTaper, SecondTaper)
    if any(
        type(Value) not in (int, float) or not IsFinite(Value) for Value in Controls
    ):
        raise ValueError("Circular side controls must be finite real numbers")
    if min(Radius, FirstMm, SecondMm) <= 0 or any(
        abs(Value) >= CirclePi / 2 for Value in (FirstTaper, SecondTaper)
    ):
        raise ValueError("Circular sides require positive dimensions and acute tapers")
    LowerRadius = Radius + SecondMm * Tangent(SecondTaper)
    UpperRadius = Radius + FirstMm * Tangent(FirstTaper)
    if not all(
        IsFinite(Value) and Value > 0
        for Value in (LowerRadius, UpperRadius, FirstMm + SecondMm)
    ):
        raise ValueError("Circular side tapers require finite positive end radii")
    if any(
        Angle != 0 and EndRadius == Radius
        for Angle, EndRadius in (
            (FirstTaper, UpperRadius),
            (SecondTaper, LowerRadius),
        )
    ):
        raise ValueError("Circular side taper disappears at coordinate precision")
    Middle = () if FirstTaper == -SecondTaper else ((Radius, 0.0),)
    return (
        (0.0, -SecondMm),
        (LowerRadius, -SecondMm),
        *Middle,
        (UpperRadius, FirstMm),
        (0.0, FirstMm),
    )
