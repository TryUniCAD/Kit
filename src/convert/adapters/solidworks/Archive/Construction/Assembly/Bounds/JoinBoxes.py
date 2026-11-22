from math import isfinite as IsFinite
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.MakeBox import (
    MakeBox,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.MergeSphere import (
    MergeSphere,
)


# native box union combines extrema independently and applies the documented farthest corner correction only after the noncontained sphere blend
def JoinBoxes(
    FirstBox: dict[str, float], SecondBox: dict[str, float]
) -> dict[str, float]:
    Minimum = tuple(
        min(SecondBox[f"b{IndexValue + 6}"], FirstBox[f"b{IndexValue + 6}"])
        for IndexValue in range(3)
    )
    Maximum = tuple(
        max(SecondBox[f"b{IndexValue + 3}"], FirstBox[f"b{IndexValue + 3}"])
        for IndexValue in range(3)
    )
    CenterValue, RadiusValue = MergeSphere(FirstBox, SecondBox)
    if RadiusValue > FirstBox["b9"] and RadiusValue > SecondBox["b9"]:
        First, Second, Third = (
            max(abs(Lower - Center), abs(Upper - Center))
            for Lower, Upper, Center in zip(Minimum, Maximum, CenterValue, strict=True)
        )
        CornerSquared = First * First + Second * Second + Third * Third
        RadiusSquared = RadiusValue * RadiusValue
        if CornerSquared + 5e-9 < RadiusSquared or (
            RadiusValue > 1e-10 and CornerSquared * 1.000000005 < RadiusSquared
        ):
            return MakeBox(
                (Minimum[0], Minimum[1], Minimum[2]),
                (Maximum[0], Maximum[1], Maximum[2]),
            )
    NumbersValue = (*CenterValue, *Maximum, *Minimum, RadiusValue)
    if not all(IsFinite(NumberValue) for NumberValue in NumbersValue):
        raise ValueError("combined assembly bounds exceed the finite native domain")
    return {
        f"b{IndexValue}": NumberValue
        for IndexValue, NumberValue in enumerate(NumbersValue)
    }
