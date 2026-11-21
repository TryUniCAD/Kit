from fractions import Fraction
from typing import TypeAlias, TypeVar

# spatial axis calculations share a fixed length representation for scalar operations
KAxisTriple: TypeAlias = tuple[float, float, float]

# vector products must keep exact intermediate arithmetic when supporting planes nearly coincide
KAxisScalar = TypeVar("KAxisScalar", float, Fraction)


# direction and incidence checks need the same oriented spatial product
def CrossAxis(
    First: tuple[KAxisScalar, KAxisScalar, KAxisScalar],
    Second: tuple[KAxisScalar, KAxisScalar, KAxisScalar],
) -> tuple[KAxisScalar, KAxisScalar, KAxisScalar]:
    FirstX, FirstY, FirstZ = First
    SecondX, SecondY, SecondZ = Second
    return (
        FirstY * SecondZ - FirstZ * SecondY,
        FirstZ * SecondX - FirstX * SecondZ,
        FirstX * SecondY - FirstY * SecondX,
    )


# intersections use exact input values because near parallel geometry magnifies premature rounding
def AxisRational(Values: KAxisTriple) -> tuple[Fraction, Fraction, Fraction]:
    return Fraction(Values[0]), Fraction(Values[1]), Fraction(Values[2])
