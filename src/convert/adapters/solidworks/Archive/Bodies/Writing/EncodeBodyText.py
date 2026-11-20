from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Strings.EncodeString import EncodeString


# authored unicode and retained ansi frames must share the existing native string codec
def EncodeBodyText(Value: object) -> bytes:
    if type(Value) is str:
        TextValue = CStringValue(Value, True)
    elif isinstance(Value, CStringValue):
        TextValue = Value
    elif type(Value) is tuple:
        PairValue = CastValue(tuple[object, ...], Value)
        if len(PairValue) != 2 or PairValue[0] != "A" or type(PairValue[1]) is not str:
            raise TypeError(
                "SOLIDWORKS body ansi text requires its explicit marker and text"
            )
        TextValue = CStringValue(PairValue[1], False)
    else:
        raise TypeError(
            "SOLIDWORKS body text requires unicode or an explicit ansi frame"
        )
    return EncodeString(TextValue, IsSourceFrame=True)
