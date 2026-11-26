from dataclasses import dataclass as DataClass
from fractions import Fraction


# exact edge positions keep validation independent from floating point intersection tolerances
@DataClass(frozen=True, slots=True)
class SweepEdge:
    IndexValue: int
    StartValue: tuple[Fraction, Fraction]
    EndValue: tuple[Fraction, Fraction]
    SlopeValue: Fraction | None

    # vertical edges require a separate range query rather than an invented ordinate
    def GetOrdinate(self, PositionX: Fraction) -> Fraction:
        if self.SlopeValue is None:
            raise ValueError("vertical polygon edge has no single sweep ordinate")
        return self.StartValue[1] + (PositionX - self.StartValue[0]) * self.SlopeValue
