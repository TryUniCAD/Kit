# native frame projections require a stable ordered scalar product in model units
def DotVector(
    First: tuple[float, float, float], Second: tuple[float, float, float]
) -> float:
    return sum(
        LeftValue * Right for LeftValue, Right in zip(First, Second, strict=True)
    )
