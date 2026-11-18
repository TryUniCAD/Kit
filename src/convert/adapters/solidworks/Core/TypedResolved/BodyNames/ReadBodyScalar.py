from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# cross stream body matching must use declared native integer fields in their original domains
def ReadBodyScalar(
    NodesValue: Mapping[int, XmtNode],
    Attributes: Mapping[str, XmtNode],
    NameValue: str,
    FieldIndex: int,
) -> int:
    Attribute = Attributes[NameValue]
    Definition = RequireXmt(NodesValue, Attribute.Integer("definition"), 80)
    TypesValue = Definition.Indexes("fields")
    FieldsValue = Attribute.Indexes("fields")
    if (
        len(TypesValue) != len(FieldsValue)
        or FieldIndex >= len(FieldsValue)
        or TypesValue[FieldIndex] != 1
    ):
        raise ValueError("native body tracking field has an unqualified type")
    Values = RequireXmt(NodesValue, FieldsValue[FieldIndex], 82).Indexes("values")
    if len(Values) != 1:
        raise ValueError("native body tracking field is not a scalar")
    return Values[0]
