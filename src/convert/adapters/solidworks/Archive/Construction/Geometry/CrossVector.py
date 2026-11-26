# oriented datum frames derive their third axis from the authored ordered tangent basis
def CrossVector(
    First: tuple[float, float, float], Second: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        First[1] * Second[2] - First[2] * Second[1],
        First[2] * Second[0] - First[0] * Second[2],
        First[0] * Second[1] - First[1] * Second[0],
    )
