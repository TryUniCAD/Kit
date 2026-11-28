from collections.abc import Mapping
from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# persisted presentation state must survive timeline normalization without recursively duplicating graph aliases
def ReadSystemState(FieldValue: object) -> object:
    if isinstance(FieldValue, ArchiveNode):
        return {
            "class": FieldValue.ClassValue.NameValue,
            "object_index": FieldValue.IndexValue,
            "node_value": ReadSystemState(FieldValue.FieldsValue.get("f08")),
        }
    if isinstance(FieldValue, Mapping):
        return {
            str(FieldName): ReadSystemState(ItemValue)
            for FieldName, ItemValue in CastValue(
                Mapping[str, object], FieldValue
            ).items()
        }
    if isinstance(FieldValue, (tuple, list)):
        return tuple(
            ReadSystemState(ItemValue)
            for ItemValue in CastValue(tuple[object, ...] | list[object], FieldValue)
        )
    if type(FieldValue) is bytes:
        return {"encoding": "hex", "bytes": FieldValue.hex()}
    if type(FieldValue) is float and not IsFinite(FieldValue):
        raise ValueError("system presentation contains a nonfinite scalar")
    if FieldValue is None or type(FieldValue) in (str, int, float, bool):
        return FieldValue
    raise ValueError("system presentation contains an unclassified field type")
