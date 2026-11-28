from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# metadata projections preserve text meaning while the graph retains its original encoding
def ReadMatText(Value: object) -> str:
    if type(Value) is str:
        return Value
    if isinstance(Value, CStringValue):
        return Value.TextValue
    if type(Value) is tuple:
        PairValue = CastValue(tuple[object, ...], Value)
        if len(PairValue) == 2 and PairValue[0] == "A" and type(PairValue[1]) is str:
            return PairValue[1]
    raise ValueError("SOLIDWORKS manager metadata requires native text")
