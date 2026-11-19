from collections.abc import Mapping
from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# typed embedded owners must remain distinct from object references before blank intent is recovered
def Fields(Value: object) -> Mapping[str, object]:
    if isinstance(Value, ArchiveNode):
        return Value.FieldsValue
    if isinstance(Value, dict):
        Dictionary = CastValue(dict[object, object], Value)
        if all(type(Key) is str for Key in Dictionary):
            return CastValue(dict[str, object], Value)
    raise BodyUnsupported("blank embedded owner has no typed fields")
