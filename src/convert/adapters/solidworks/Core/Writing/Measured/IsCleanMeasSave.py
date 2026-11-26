from typing import cast as CastValue


# a clean save must report exact success and separate zero error and warning counts
def IsCleanMeasSave(Value: object) -> bool:
    if type(Value) is not list:
        return False
    Items = CastValue(list[object], Value)
    return (
        len(Items) == 3
        and Items[0] is True
        and all(type(ItemValue) is int and ItemValue == 0 for ItemValue in Items[1:])
    )
