from collections.abc import Callable, Container
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Expressions.IsValueCompared import (
    IsValueCompared,
)


# chained field comparisons must short circuit without evaluating unrelated archive branches
def IsExprCompared(
    Arguments: tuple[object, ...], ReadValue: Callable[[tuple[object, ...]], object]
) -> bool:
    NamesValue = CastValue(tuple[str, ...], Arguments[0])
    LeftValue = ReadValue(CastValue(tuple[object, ...], Arguments[1]))
    for NameValue, Expression in zip(NamesValue, Arguments[2:], strict=True):
        RightValue = ReadValue(CastValue(tuple[object, ...], Expression))
        if NameValue in ("In", "NotIn"):
            IsCompared = LeftValue in CastValue(Container[object], RightValue)
            IsCompared = not IsCompared if NameValue == "NotIn" else IsCompared
        else:
            IsCompared = IsValueCompared(NameValue, LeftValue, RightValue)
        if not IsCompared:
            return False
        LeftValue = RightValue
    return True
