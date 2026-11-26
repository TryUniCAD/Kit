from collections.abc import Mapping, Sequence
from typing import cast as CastValue


# embedded records carry fields without a separately allocated class slot
def RequireRecord(RecordValue: object) -> Mapping[str, object]:
    if not isinstance(RecordValue, Mapping):
        raise ValueError("SOLIDWORKS graph expected an embedded record")
    return CastValue(Mapping[str, object], RecordValue)


# identity and flag fields require integers from their typed wire owners
def FieldInt(Values: Mapping[str, object], FieldName: str) -> int:
    ItemValue = Values.get(FieldName)
    if type(ItemValue) is not int:
        raise ValueError(f"SOLIDWORKS graph expected integer {FieldName}")
    return ItemValue


# native names must have a real serialized owner before they identify an object
def FieldText(Values: Mapping[str, object], FieldName: str) -> str:
    ItemValue = Values.get(FieldName)
    if type(ItemValue) is not str or not ItemValue:
        raise ValueError(f"SOLIDWORKS graph expected text {FieldName}")
    return ItemValue


# collection framing must retain complete ordered records for ownership checks
def ReadRows(RowsValue: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(RowsValue, (list, tuple)):
        raise ValueError("SOLIDWORKS graph expected an ordered record collection")
    return tuple(
        RequireRecord(ItemValue) for ItemValue in CastValue(Sequence[object], RowsValue)
    )
