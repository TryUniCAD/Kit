from collections.abc import Mapping
from typing import cast as CastValue


# a native save may serialize present zero length arrays without adding any reference semantics
def IsEndListEmpty(FieldsValue: Mapping[str, object], NameValue: str) -> bool:
    Present = FieldsValue.get("has_" + NameValue)
    RowsValue = FieldsValue.get(NameValue)
    if type(Present) is not int:
        return False
    if Present == 0:
        return RowsValue is None
    if Present != 1 or not isinstance(RowsValue, Mapping):
        return False
    RecordValue = CastValue(Mapping[str, object], RowsValue)
    CountValue, ItemsValue = RecordValue.get("n"), RecordValue.get("items")
    return (
        type(CountValue) is int
        and CountValue == 0
        and type(ItemsValue) in (list, tuple)
        and not ItemsValue
    )
