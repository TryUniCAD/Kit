from math import sqrt as SqrtValue


# native quaternion matrices normalize each row with the same arithmetic grouping as their original computation
def ViewMatrix(Quaternion: tuple[float, float, float, float]) -> dict[str, float]:
    ValueX, ValueY, ValueZ, ValueW = Quaternion
    DoubleX, DoubleY, DoubleZ = ValueX + ValueX, ValueY + ValueY, ValueZ + ValueZ
    SquareX, MixedXY, MixedXZ = ValueX * DoubleX, ValueX * DoubleY, ValueX * DoubleZ
    SquareY, MixedYZ, SquareZ = ValueY * DoubleY, ValueY * DoubleZ, ValueZ * DoubleZ
    MixedWX, MixedWY, MixedWZ = ValueW * DoubleX, ValueW * DoubleY, ValueW * DoubleZ
    RowsValue = (
        (1 - (SquareZ + SquareY), MixedXY - MixedWZ, MixedWY + MixedXZ),
        (MixedWZ + MixedXY, 1 - (SquareZ + SquareX), MixedYZ - MixedWX),
        (MixedXZ - MixedWY, MixedWX + MixedYZ, 1 - (SquareY + SquareX)),
    )
    ValuesValue: list[float] = []
    for RowValue in RowsValue:
        LengthValue = (
            RowValue[0] * RowValue[0] + RowValue[1] * RowValue[1]
        ) + RowValue[2] * RowValue[2]
        if LengthValue < 1e-17:
            raise ValueError("canonical view rotation produced a zero row")
        InverseValue = 1.0 / SqrtValue(LengthValue)
        ValuesValue.extend(Coordinate * InverseValue for Coordinate in RowValue)
    return {
        f"m{IndexValue}": Coordinate
        for IndexValue, Coordinate in enumerate(ValuesValue)
    }
