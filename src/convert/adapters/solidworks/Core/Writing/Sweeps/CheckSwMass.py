from math import isclose as IsClose, pi as PiValue


# every observed state must match the physical quarter tube defined by its own two live drivers
def CheckSwMass(StateValue: tuple[float, ...], DensityValue: float) -> None:
    Diameter, PathRadius, Volume, AreaValue, MassValue, CenterX, CenterY, CenterZ = (
        StateValue
    )
    SectionRadius = Diameter / 2.0
    if not 0.001 <= SectionRadius < PathRadius <= 0.15:
        raise ValueError(
            "SOLIDWORKS sweep measurement exceeds the measured radius profile"
        )
    ArcAngle = PiValue / 2.0
    ExpectedVolume = PiValue * SectionRadius**2 * PathRadius * ArcAngle
    ExpectedArea = (
        2.0 * PiValue * SectionRadius * (PathRadius * ArcAngle + SectionRadius)
    )
    ExpectedX = (PathRadius + SectionRadius**2 / (4.0 * PathRadius)) / ArcAngle
    if abs(CenterZ) > 1e-11 or not all(
        IsClose(Measured, Expected, rel_tol=5e-7)
        for Measured, Expected in (
            (Volume, ExpectedVolume),
            (AreaValue, ExpectedArea),
            (MassValue, DensityValue * ExpectedVolume),
            (CenterX, ExpectedX),
            (CenterY, PathRadius - ExpectedX),
        )
    ):
        raise ValueError(
            "SOLIDWORKS sweep measurement disagrees with quarter tube geometry"
        )
