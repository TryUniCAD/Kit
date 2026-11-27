from math import fsum as SumValues, pi as CirclePi


# exact radial integrals retain the joint contribution and signed axial first moment
def DualMoments(
    Meridian: tuple[tuple[float, float], ...],
) -> tuple[float, float, float, float]:
    Volumes: list[float] = []
    Moments: list[float] = []
    Radial: list[float] = []
    Axial: list[float] = []
    for (Radius, Lower), (UpperRadius, Upper) in zip(
        Meridian[1:-2], Meridian[2:-1], strict=True
    ):
        Height, Delta = Upper - Lower, UpperRadius - Radius
        Zeroth = Height * (Radius**2 + Radius * UpperRadius + UpperRadius**2) / 3
        First = Height**2 * (Radius**2 / 2 + 2 * Radius * Delta / 3 + Delta**2 / 4)
        Second = Height**3 * (Radius**2 / 3 + Radius * Delta / 2 + Delta**2 / 5)
        Fourth = (
            Height
            * sum(Radius ** (4 - Index) * UpperRadius**Index for Index in range(5))
            / 5
        )
        Volumes.append(CirclePi * Zeroth)
        Moments.append(CirclePi * (Lower * Zeroth + First))
        Radial.append(CirclePi * Fourth / 4)
        Axial.append(CirclePi * (Lower**2 * Zeroth + 2 * Lower * First + Second))
    return SumValues(Volumes), SumValues(Moments), SumValues(Radial), SumValues(Axial)
