from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalXmtProfile import (
    KLocalLimit,
)
from convert.adapters.solidworks.Archive.Partition.XmtField import XmtField
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# framing must derive each array extent from the supplied typed members
def GetXmtField(
    NodeValue: XmtNode, FieldValue: XmtField
) -> tuple[int, tuple[object, ...]]:
    RawValue = NodeValue.FieldsValue[FieldValue.NameValue]
    if FieldValue.EncodingValue == "c":
        if type(RawValue) is not str or not RawValue.isascii():
            raise ValueError(
                f"kernel text field is unqualified: {FieldValue.NameValue}"
            )
        CountValue = len(RawValue)
        MembersValue: tuple[object, ...] = (RawValue,)
    elif FieldValue.CountValue:
        if type(RawValue) is not tuple:
            raise ValueError(
                f"kernel array field is unqualified: {FieldValue.NameValue}"
            )
        MembersValue = CastValue(tuple[object, ...], RawValue)
        CountValue = len(MembersValue)
    else:
        CountValue, MembersValue = 1, (RawValue,)
    if CountValue > KLocalLimit or (
        FieldValue.CountValue != 1 and CountValue != (FieldValue.CountValue or 1)
    ):
        raise ValueError(f"kernel field count is unqualified: {FieldValue.NameValue}")
    return CountValue, MembersValue
