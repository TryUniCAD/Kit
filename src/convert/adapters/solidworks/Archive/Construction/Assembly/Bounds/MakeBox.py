from math import isfinite as IsFinite, sqrt as SquareRoot


# ordinary geometry bounds derive their center sphere and extrema from independently authored generated coordinates rather than saved model caches
def MakeBox(
    Minimum: tuple[float, float, float], Maximum: tuple[float, float, float]
) -> dict[str, float]:
    if any(Lower > Upper for Lower, Upper in zip(Minimum, Maximum, strict=True)):
        raise ValueError("generated bounds minimum exceeds maximum")
    CenterValue = tuple(
        (Lower + Upper) * 0.5 for Lower, Upper in zip(Minimum, Maximum, strict=True)
    )
    WidthValue, HeightValue, DepthValue = (
        Upper - Lower for Lower, Upper in zip(Minimum, Maximum, strict=True)
    )
    RadiusValue = (
        SquareRoot(
            WidthValue * WidthValue
            + HeightValue * HeightValue
            + DepthValue * DepthValue
        )
        * 0.5
    )
    NumbersValue = (*CenterValue, *Maximum, *Minimum, RadiusValue)
    if not all(IsFinite(NumberValue) for NumberValue in NumbersValue):
        raise ValueError("generated bounds exceed the finite native domain")
    return {
        f"b{IndexValue}": NumberValue
        for IndexValue, NumberValue in enumerate(NumbersValue)
    }
