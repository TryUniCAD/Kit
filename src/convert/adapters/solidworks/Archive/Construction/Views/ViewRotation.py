from convert.adapters.solidworks.Archive.Construction.Views.RoundViewSeries import (
    RoundViewSeries,
)


# native view rotation uses the negative half angle and must not inherit a library convention silently
def ViewRotation(AxisName: str, AngleValue: float) -> tuple[float, float, float, float]:
    HalfAngle = AngleValue * -0.5
    SineValue = RoundViewSeries(HalfAngle, 1)
    CosineValue = RoundViewSeries(HalfAngle, 0)
    if AxisName == "x":
        return SineValue, 0.0 * SineValue, 0.0 * SineValue, CosineValue
    if AxisName == "y":
        return 0.0 * SineValue, SineValue, 0.0 * SineValue, CosineValue
    raise ValueError("canonical view rotation requires a recovered x or y axis")
