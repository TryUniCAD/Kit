from struct import pack as PackValue

from convert.Geometry.Parasolid import WritePointerMut
from convert.adapters.solidworks.Archive.Partition.LocalWrite.GetXmtField import (
    GetXmtField,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.PutXmtValueMut import (
    PutXmtValueMut,
)
from convert.adapters.solidworks.Archive.Partition.SchemaHeader import SchemaHeader
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Partition.XmtShape import XmtShape


# canonical records need effective schema order and matching whole field inventories
def WriteXmtNodeMut(
    OutputValue: bytearray,
    NodeValue: XmtNode,
    ShapeValue: XmtShape,
    SeenKinds: set[int],
) -> None:
    if set(NodeValue.FieldsValue) != {
        FieldValue.NameValue for FieldValue in ShapeValue.FieldsValue
    }:
        raise ValueError(
            f"local kernel node has missing or unknown fields: {ShapeValue.NameValue}"
        )
    FieldsValue = tuple(
        (FieldValue, GetXmtField(NodeValue, FieldValue))
        for FieldValue in ShapeValue.FieldsValue
    )
    OutputValue.extend(PackValue(">H", NodeValue.KindValue))
    if NodeValue.KindValue not in SeenKinds:
        OutputValue.extend(SchemaHeader(ShapeValue))
        SeenKinds.add(NodeValue.KindValue)
    for FieldValue, (CountValue, _) in FieldsValue:
        if FieldValue.CountValue == 1:
            OutputValue.extend(PackValue(">I", CountValue))
    WritePointerMut(OutputValue, NodeValue.IndexValue)
    for FieldValue, (_, MembersValue) in FieldsValue:
        for MemberValue in MembersValue:
            PutXmtValueMut(OutputValue, FieldValue.EncodingValue, MemberValue)
