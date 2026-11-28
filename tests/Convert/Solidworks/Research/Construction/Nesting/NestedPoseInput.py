from math import cos as CosValue, radians as RadianValue, sin as SinValue


# authored noncommuting rotations must remain independent from the sdk frame and bounds implementations used by the recursive writer
def NestedPoseInput(
    TargetName: str,
    NameValue: str,
    AxisValue: str,
    AngleValue: float,
    OriginValue: tuple[float, float, float],
) -> dict[str, object]:
    AxisIndex = "xyz".index(AxisValue)
    FirstIndex, SecondIndex = (AxisIndex + 1) % 3, (AxisIndex + 2) % 3
    MatrixValue = [0.0] * 9
    MatrixValue[AxisIndex * 3 + AxisIndex] = 1.0
    AngleValue = RadianValue(AngleValue)
    MatrixValue[FirstIndex * 3 + FirstIndex] = MatrixValue[
        SecondIndex * 3 + SecondIndex
    ] = CosValue(AngleValue)
    MatrixValue[FirstIndex * 3 + SecondIndex] = SinValue(AngleValue)
    MatrixValue[SecondIndex * 3 + FirstIndex] = -SinValue(AngleValue)
    return {
        "target": TargetName,
        "occurrence": {
            "name": NameValue,
            "origin": list(OriginValue),
            "u": MatrixValue[:3],
            "v": MatrixValue[3:6],
        },
    }
