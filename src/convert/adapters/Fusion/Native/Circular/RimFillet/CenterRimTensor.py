from math import isfinite as IsFinite


# the parallel axis theorem couples every origin tensor component to its already checked centroid
def CenterRimTensor(
    Volume: float,
    Center: tuple[float, float, float],
    Diagonal: tuple[float, float, float],
    CrossTerms: tuple[float, float, float],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    Central = tuple(
        Diagonal[Index]
        - Volume * sum(Center[Other] ** 2 for Other in range(3) if Other != Index)
        for Index in range(3)
    )
    Products = tuple(
        Value + Volume * Center[First] * Center[Second]
        for Value, (First, Second) in zip(
            CrossTerms, ((0, 1), (0, 2), (1, 2)), strict=True
        )
    )
    if not all(IsFinite(Value) for Value in (*Central, *Products)) or min(Central) <= 0:
        raise ValueError("Native rim central tensor exceeds finite solid geometry")
    return Central, Products
