from math import cos as CosValue, sin as SinValue


# native view rotation uses the negative half angle and must not inherit a library convention silently
def ViewRotation(AxisName: str, AngleValue: float) -> tuple[float, float, float, float]:
    SineValue, CosineValue = SinValue(AngleValue * -0.5), CosValue(AngleValue * -0.5)
    if AxisName == "x":
        return SineValue, 0.0 * SineValue, 0.0 * SineValue, CosineValue
    if AxisName == "y":
        return 0.0 * SineValue, SineValue, 0.0 * SineValue, CosineValue
    raise ValueError("canonical view rotation requires a recovered x or y axis")
