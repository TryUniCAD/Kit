from typing import cast as CastValue


# native receipt vectors require a bounded concrete json array and exact dimension
def BoxMeasArray(Value: object, CountValue: int) -> tuple[object, ...]:
    if type(Value) is not list:
        raise ValueError("attached box measurement requires an actual numeric array")
    Items = CastValue(list[object], Value)
    if len(Items) != CountValue:
        raise ValueError("attached box measurement has an incomplete numeric array")
    return tuple(Items)
