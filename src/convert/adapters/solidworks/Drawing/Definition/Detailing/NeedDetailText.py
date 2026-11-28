from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# native model and component keys must retain their original text without guessed normalization
def NeedDetailText(Value: object) -> str:
    if isinstance(Value, CStringValue):
        Value = CastValue(object, Value.TextValue)
    if isinstance(Value, str):
        return Value
    raise BodyUnsupported("drawing detailing index requires native text keys")
