from math import isclose as IsClose


# the offline comparator allows native roundoff while retaining each observed body and driver
def IsSameMeasState(
    FirstValue: tuple[int, tuple[float, ...]],
    OtherValue: tuple[int, tuple[float, ...]],
) -> bool:
    return FirstValue[0] == OtherValue[0] and all(
        IsClose(First, Other, rel_tol=5e-7, abs_tol=(1e-11 if Index >= 3 else 0.0))
        for Index, (First, Other) in enumerate(
            zip(FirstValue[1], OtherValue[1], strict=True)
        )
    )
