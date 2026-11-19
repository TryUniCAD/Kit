from dataclasses import fields as DataclassFields
from dataclasses import is_dataclass as IsDataClass
from uuid import UUID
from typing import cast as CastValue
from collections.abc import Sequence

from interchange.serialization.OptionalFields import KOmitNullField


# reconstructed semantic inputs must survive document serialization without opaque bytes or unsupported objects
def Plain(Value: object) -> object:
    if isinstance(Value, UUID):
        return str(Value)
    if IsDataClass(Value) and not isinstance(Value, type):
        Members: dict[str, object] = {}
        for FieldValue in DataclassFields(Value):
            Member = CastValue(object, getattr(Value, FieldValue.name))
            if Member is None and FieldValue.metadata.get(KOmitNullField):
                continue
            Members[FieldValue.name] = Plain(Member)
        return Members
    if isinstance(Value, dict):
        MappingValue = CastValue(dict[object, object], Value)
        if any(type(Key) is not str for Key in MappingValue):
            raise TypeError("blank intent metadata has a nontext key")
        return {CastValue(str, Key): Plain(Item) for Key, Item in MappingValue.items()}
    if isinstance(Value, (list, tuple)):
        return [Plain(Item) for Item in CastValue(Sequence[object], Value)]
    if Value is None or type(Value) in (str, int, float, bool):
        return Value
    raise TypeError("blank intent metadata contains an unsupported value")
