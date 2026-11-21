from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber,
)


# portable scale terms must retain exact authored values within the independently qualified integral sheet constructor domain
def ReadSheetRatio(RatioValue: tuple[float, float]) -> tuple[int, int]:
    if type(RatioValue) is not tuple or len(RatioValue) != 2:
        raise ValueError(
            "neutral blank drawing requires two explicit sheet scale terms"
        )
    ValuesValue = tuple(NeedDrawNumber(Value) for Value in RatioValue)
    if any(not Value.is_integer() or not 1 <= Value <= 999999 for Value in ValuesValue):
        raise ValueError(
            "neutral blank drawing sheet scale is outside the qualified integral domain"
        )
    return int(ValuesValue[0]), int(ValuesValue[1])
