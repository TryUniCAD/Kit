from collections.abc import Callable
from typing import cast as CastValue


# semantic sequences must preserve complete arity and every nested typed owner across public json transport
def ReadBlankTuple(
    Arguments: tuple[object, ...],
    Value: object,
    ReadValue: Callable[[object, object], object],
) -> tuple[object, ...]:
    if type(Value) is not list:
        raise ValueError("blank metadata tuple must retain its complete JSON sequence")
    Items = CastValue(list[object], Value)
    if len(Arguments) == 2 and Arguments[1] is Ellipsis:
        return tuple(ReadValue(Arguments[0], ItemValue) for ItemValue in Items)
    if len(Items) != len(Arguments):
        raise ValueError("blank metadata tuple arity differs")
    return tuple(
        ReadValue(Argument, ItemValue)
        for Argument, ItemValue in zip(Arguments, Items, strict=True)
    )
