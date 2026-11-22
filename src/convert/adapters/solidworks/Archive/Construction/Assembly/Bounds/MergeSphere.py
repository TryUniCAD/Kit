from math import isfinite as IsFinite, sqrt as SquareRoot


# native sphere union preserves containment branches before shifting the current center according to the two independently transformed sphere radii
def MergeSphere(
    FirstBox: dict[str, float], SecondBox: dict[str, float]
) -> tuple[tuple[float, float, float], float]:
    CenterValue = (FirstBox["b0"], FirstBox["b1"], FirstBox["b2"])
    Incoming = (SecondBox["b0"], SecondBox["b1"], SecondBox["b2"])
    DeltaValue = tuple(
        Second - First for First, Second in zip(CenterValue, Incoming, strict=True)
    )
    First, Second, Third = DeltaValue
    DistanceValue = SquareRoot(First * First + Second * Second + Third * Third)
    RadiusValue, OtherRadius = FirstBox["b9"], SecondBox["b9"]
    UnionRadius = (RadiusValue + OtherRadius + DistanceValue) * 0.5
    if not IsFinite(UnionRadius):
        raise ValueError("combined sphere exceeds the finite native domain")
    if UnionRadius <= RadiusValue:
        return CenterValue, RadiusValue
    if UnionRadius <= OtherRadius:
        return Incoming, OtherRadius
    WeightValue = (UnionRadius - RadiusValue) / DistanceValue
    NumbersValue = tuple(
        Center + Delta * WeightValue
        for Center, Delta in zip(CenterValue, DeltaValue, strict=True)
    )
    return (NumbersValue[0], NumbersValue[1], NumbersValue[2]), UnionRadius
