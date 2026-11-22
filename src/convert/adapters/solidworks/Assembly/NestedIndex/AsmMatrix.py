from interchange.assembly.TransformMatrix import TransformMatrix


# portable placement transposes the native rows and converts only the three translation words
def AsmMatrix(Values: tuple[float, ...]) -> TransformMatrix:
    return TransformMatrix(
        (
            Values[0],
            Values[4],
            Values[8],
            Values[12] * 1000.0,
            Values[1],
            Values[5],
            Values[9],
            Values[13] * 1000.0,
            Values[2],
            Values[6],
            Values[10],
            Values[14] * 1000.0,
            Values[3],
            Values[7],
            Values[11],
            Values[15],
        )
    )
