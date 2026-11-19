from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylAttr import (
    ReadCylAttr,
)


# native face identification must use the typed integer lane rather than opaque pointer values
def ReadCylWords(
    NodesValue: Mapping[int, XmtNode], FaceValue: XmtNode, FieldIndex: int = 2
) -> tuple[int, ...]:
    Attribute = ReadCylAttr(NodesValue, FaceValue, "FACE_ID_2001")
    Definition = RequireXmt(NodesValue, Attribute.Integer("definition"), 80)
    FieldsValue = Attribute.Indexes("fields")
    if (
        Definition.Indexes("fields") != (9, 9, 1, 1)
        or len(FieldsValue) != 4
        or FieldsValue[:2] != (0, 0)
        or FieldIndex not in (2, 3)
    ):
        raise ValueError("concentric face identity uses unqualified typed lanes")
    return RequireXmt(NodesValue, FieldsValue[FieldIndex], 82).Indexes("values")
