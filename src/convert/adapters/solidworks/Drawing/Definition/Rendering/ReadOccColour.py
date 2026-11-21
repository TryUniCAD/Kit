from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Drawing.Definition.Rendering.NeedViewMap import (
    NeedViewMap,
)
from convert.adapters.solidworks.Drawing.Definition.Rendering.OccColour import OccColour


# native occurrence identifiers and colour words require their separate signed wire domains
def ReadOccColour(Value: object) -> OccColour:
    FieldsValue = NeedViewMap(Value)
    if set(FieldsValue) != {"key", "value"}:
        raise BodyUnsupported("drawing view state has unknown occurrence colour fields")
    Occurrence = FieldsValue.get("key")
    ColourWord = FieldsValue.get("value")
    if (
        type(Occurrence) is not int
        or not -(1 << 31) <= Occurrence < (1 << 31)
        or type(ColourWord) is not int
        or not 0 <= ColourWord < (1 << 32)
    ):
        raise BodyUnsupported("drawing view state has invalid occurrence colour words")
    return OccColour(Occurrence, ColourWord)
