from math import isclose as IsClose

from convert.Geometry.SweptTube.QuarterMetric import MeasureQuarter


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
    Expected = MeasureQuarter(SectionRadius, PathRadius)
    if abs(CenterZ) > 1e-11 or not all(
        IsClose(Measured, Derived, rel_tol=5e-7)
        for Measured, Derived in (
            (Volume, Expected.VolumeValue),
            (AreaValue, Expected.AreaValue),
            (MassValue, DensityValue * Expected.VolumeValue),
            (CenterX, Expected.CenterValue.x),
            (CenterY, Expected.CenterValue.y),
        )
    ):
        raise ValueError(
            "SOLIDWORKS sweep measurement disagrees with quarter tube geometry"
        )
