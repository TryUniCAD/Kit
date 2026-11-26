from math import isfinite as IsFinite, sqrt as SquareRoot

from convert.adapters.solidworks.Archive.Construction.Geometry.DotVector import (
    DotVector,
)


# frame axes must have finite nonzero length before their orientation can produce a native transform
def UnitVector(Value: tuple[float, float, float]) -> tuple[float, float, float]:
    Length = SquareRoot(DotVector(Value, Value))
    if not IsFinite(Length) or Length == 0:
        raise ValueError("native frame axes require finite nonzero length")
    return Value[0] / Length, Value[1] / Length, Value[2] / Length
