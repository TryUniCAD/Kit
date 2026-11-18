from math import sqrt as SquareRoot

from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber,
)


# native boxes store centre extrema and enclosing radius derived from the actual geometric bounds
def MakeViewBox(
    Minimum: tuple[float, ...], Maximum: tuple[float, ...]
) -> dict[str, float]:
    if len(Minimum) != 3 or len(Maximum) != 3:
        raise ValueError("drawing view bounds require three dimensional extrema")
    LowValue = tuple(NeedDrawNumber(Value) for Value in Minimum)
    HighValue = tuple(NeedDrawNumber(Value) for Value in Maximum)
    if any(
        LowNumber > HighNumber
        for LowNumber, HighNumber in zip(LowValue, HighValue, strict=True)
    ):
        raise ValueError("drawing view bounds have reversed extrema")
    Centre = tuple(
        (LowNumber + HighNumber) * 0.5
        for LowNumber, HighNumber in zip(LowValue, HighValue, strict=True)
    )
    Difference = tuple(
        HighNumber - LowNumber
        for LowNumber, HighNumber in zip(LowValue, HighValue, strict=True)
    )
    DeltaX, DeltaY, DeltaZ = Difference
    Radius = SquareRoot(DeltaX * DeltaX + DeltaY * DeltaY + DeltaZ * DeltaZ) * 0.5
    return {
        f"b{Index}": NeedDrawNumber(Value)
        for Index, Value in enumerate((*Centre, *HighValue, *LowValue, Radius))
    }
