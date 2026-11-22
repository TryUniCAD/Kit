from collections.abc import Callable
from typing import cast as CastValue


# native boolean selection must preserve its conditional evaluation and returned scalar
def ExprLogic(
    ActionValue: str,
    Arguments: tuple[object, ...],
    ReadValue: Callable[[tuple[object, ...]], object],
) -> object:
    if ActionValue == "select":
        Condition = ReadValue(CastValue(tuple[object, ...], Arguments[0]))
        return ReadValue(
            CastValue(tuple[object, ...], Arguments[1 if Condition else 2])
        )
    Result: object = False
    for Expression in Arguments:
        Result = ReadValue(CastValue(tuple[object, ...], Expression))
        if bool(Result) == (ActionValue == "Or"):
            return Result
    return Result
