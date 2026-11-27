from collections.abc import Sized
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Expressions.ExprBinary import ExprBinary
from convert.adapters.solidworks.Archive.Expressions.ExprUnary import ExprUnary


# numeric format helpers require fixed operators without evaluating functions from document content
def ExprMath(ActionValue: str, Values: tuple[object, ...]) -> object:
    if ActionValue in (
        "Add",
        "Sub",
        "Mult",
        "FloorDiv",
        "BitAnd",
        "BitOr",
        "BitXor",
        "LShift",
        "RShift",
    ):
        return ExprBinary(ActionValue, Values[0], Values[1])
    if ActionValue in ("USub", "UAdd", "Invert", "Not"):
        return ExprUnary(ActionValue, Values[0])
    if ActionValue == "bool":
        return bool(Values[0])
    if ActionValue == "int":
        return int(CastValue(int | float, Values[0]))
    if ActionValue == "len":
        return len(CastValue(Sized, Values[0]))
    Numbers = CastValue(tuple[int | float, ...], Values)
    if ActionValue == "max":
        return max(Numbers)
    if ActionValue == "min":
        return min(Numbers)
    raise ValueError(f"unsupported native arithmetic {ActionValue}")
