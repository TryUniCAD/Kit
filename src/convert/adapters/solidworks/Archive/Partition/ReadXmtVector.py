from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# geometry binding requires complete spatial coordinates without implicit scalar conversion
def ReadXmtVector(NodeValue: XmtNode, NameValue: str) -> tuple[float, float, float]:
    FieldValue = NodeValue.FieldsValue[NameValue]
    if not isinstance(FieldValue, tuple):
        raise ValueError("kernel field is not a spatial vector")
    MembersValue = CastValue(tuple[object, ...], FieldValue)
    if len(MembersValue) != 3 or any(
        type(MemberValue) is not float for MemberValue in MembersValue
    ):
        raise ValueError("kernel field is not a spatial vector")
    return CastValue(tuple[float, float, float], FieldValue)
