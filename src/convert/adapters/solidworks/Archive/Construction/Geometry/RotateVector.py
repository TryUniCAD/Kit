# native placement matrices act on row vectors independently from their translation component
def RotateVector(
    Matrix: tuple[float, ...], Value: tuple[float, float, float]
) -> tuple[float, float, float]:
    Result = tuple(
        sum(Value[AxisIndex] * Matrix[AxisIndex * 3 + Index] for AxisIndex in range(3))
        for Index in range(3)
    )
    return Result[0], Result[1], Result[2]
