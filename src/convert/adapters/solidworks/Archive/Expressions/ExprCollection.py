from collections.abc import Callable
from typing import cast as CastValue


# collection literals belong to format predicates without becoming document supplied lookup programs
def ExprCollection(
    ActionValue: str,
    Arguments: tuple[object, ...],
    ReadValue: Callable[[tuple[object, ...]], object],
) -> object:
    RowsValue = CastValue(tuple[object, ...], Arguments[0])
    if ActionValue == "sequence":
        return tuple(
            ReadValue(CastValue(tuple[object, ...], Expression))
            for Expression in RowsValue
        )
    Result: dict[object, object] = {}
    for RowValue in RowsValue:
        KeyRule, ValueRule = CastValue(
            tuple[tuple[object, ...], tuple[object, ...]], RowValue
        )
        Result[ReadValue(KeyRule)] = ReadValue(ValueRule)
    return Result
