from fractions import Fraction


# exact turns distinguish true contact from roundoff near adjacent polygon vertices
def RingTurn(
    Alpha: tuple[Fraction, Fraction],
    Bravo: tuple[Fraction, Fraction],
    Charlie: tuple[Fraction, Fraction],
) -> Fraction:
    return (Bravo[0] - Alpha[0]) * (Charlie[1] - Alpha[1]) - (Bravo[1] - Alpha[1]) * (
        Charlie[0] - Alpha[0]
    )


# collinear contact requires both coordinate ranges rather than a tolerance guess
def IsOnRingEdge(
    Alpha: tuple[Fraction, Fraction],
    Bravo: tuple[Fraction, Fraction],
    PointValue: tuple[Fraction, Fraction],
) -> bool:
    return min(Alpha[0], Bravo[0]) <= PointValue[0] <= max(Alpha[0], Bravo[0]) and min(
        Alpha[1], Bravo[1]
    ) <= PointValue[1] <= max(Alpha[1], Bravo[1])


# nonadjacent contacts and crossings cannot define the selected simple closed native profile
def IsRingCrossing(
    Alpha: tuple[Fraction, Fraction],
    Bravo: tuple[Fraction, Fraction],
    Charlie: tuple[Fraction, Fraction],
    Delta: tuple[Fraction, Fraction],
) -> bool:
    FirstValue, SecondValue = RingTurn(Alpha, Bravo, Charlie), RingTurn(
        Alpha, Bravo, Delta
    )
    ThirdValue, FourthValue = RingTurn(Charlie, Delta, Alpha), RingTurn(
        Charlie, Delta, Bravo
    )
    if ((FirstValue > 0 > SecondValue) or (SecondValue > 0 > FirstValue)) and (
        (ThirdValue > 0 > FourthValue) or (FourthValue > 0 > ThirdValue)
    ):
        return True
    return (
        FirstValue == 0
        and IsOnRingEdge(Alpha, Bravo, Charlie)
        or SecondValue == 0
        and IsOnRingEdge(Alpha, Bravo, Delta)
        or ThirdValue == 0
        and IsOnRingEdge(Charlie, Delta, Alpha)
        or FourthValue == 0
        and IsOnRingEdge(Charlie, Delta, Bravo)
    )
