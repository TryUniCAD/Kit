from fractions import Fraction
from typing import Literal


# measured view bytes require the same rounded half angle terms on every platform
def RoundViewSeries(HalfAngle: float, TermPower: Literal[0, 1]) -> float:
    if not -2.0 <= HalfAngle <= 2.0:
        raise ValueError("canonical view half angle is outside the bounded series")
    if HalfAngle == 0.0:
        return HalfAngle if TermPower else 1.0

    ExactAngle = Fraction(HalfAngle)
    NegSquare = -(ExactAngle * ExactAngle)
    TermValue = ExactAngle if TermPower else Fraction(1)
    SeriesSum = TermValue
    PriorSum = SeriesSum
    for IndexValue in range(1, 25):
        Exponent = 2 * IndexValue + TermPower
        TermValue *= NegSquare / ((Exponent - 1) * Exponent)
        PriorSum = SeriesSum
        SeriesSum += TermValue

    RoundedValue = float(SeriesSum)
    if float(PriorSum).hex() != RoundedValue.hex():
        raise ValueError("canonical view series did not establish unique rounding")
    return RoundedValue
