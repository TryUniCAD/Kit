from collections.abc import MutableMapping
from typing import cast as CastValue


# native embedded records must keep their actual owning field instead of a reconstructed value copy
def ReadFields(
    FieldsValue: MutableMapping[str, object], FieldName: str
) -> MutableMapping[str, object]:
    Value = FieldsValue[FieldName]
    if not isinstance(Value, MutableMapping):
        raise TypeError(f"ANSI construction requires embedded record {FieldName}")
    if any(type(KeyValue) is not str for KeyValue in Value):
        raise TypeError("ANSI embedded field names must be text")
    return CastValue(MutableMapping[str, object], Value)
