from math import fsum as SumValues, hypot as Hypot, isfinite as IsFinite
from math import pi as CirclePi


# each side contributes its own signed first moment without an internal cap
def DualMeasure(
    Meridian: tuple[tuple[float, float], ...],
) -> tuple[float, float, float]:
    Volumes: list[float] = []
    Moments: list[float] = []
    Areas: list[float] = []
    for (FirstRadius, Lower), (SecondRadius, Upper) in zip(
        Meridian[1:-2], Meridian[2:-1], strict=True
    ):
        Height = Upper - Lower
        CrossSum = FirstRadius**2 + FirstRadius * SecondRadius + SecondRadius**2
        Volume = CirclePi * Height * CrossSum / 3
        Center = Lower + Height * (
            FirstRadius**2 + 2 * FirstRadius * SecondRadius + 3 * SecondRadius**2
        ) / (4 * CrossSum)
        Volumes.append(Volume)
        Moments.append(Volume * Center)
        Areas.append(
            CirclePi
            * (FirstRadius + SecondRadius)
            * Hypot(Height, SecondRadius - FirstRadius)
        )
    Volume = SumValues(Volumes)
    AreaValue = SumValues(
        (*Areas, CirclePi * Meridian[1][0] ** 2, CirclePi * Meridian[-2][0] ** 2)
    )
    Center = SumValues(Moments) / Volume
    if not all(IsFinite(Value) for Value in (Volume, AreaValue, Center)):
        raise ValueError("Circular side measures exceed finite geometry")
    return Volume, AreaValue, Center
