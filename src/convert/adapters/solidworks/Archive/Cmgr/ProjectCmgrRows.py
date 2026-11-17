from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrRows import ReadCmgrRows
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrText import ReadCmgrText
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# configuration captions and descriptions need their actual owning nodes and pointer identities
def ProjectCmgrRows(RootValue: ArchiveNode) -> tuple[Mapping[str, object], ...]:
    RowsValue: list[Mapping[str, object]] = []
    for NodeValue in ReadCmgrRows(RootValue):
        FieldsValue = NodeValue.FieldsValue
        NameNode = ArchiveNode.RequireNode(FieldsValue.get("f18"))
        if NameNode.ClassValue != RuntimeClass("moNodeName_c", 1):
            raise ValueError("SOLIDWORKS configuration name has an unsupported owner")
        RowsValue.append(
            {
                "name": ReadCmgrText(NameNode.FieldsValue["f08"]),
                "comment": ReadCmgrText(FieldsValue["f4a8"]),
                "alternate_name": ReadCmgrText(FieldsValue["f498"]),
                "feature_description": ReadCmgrText(FieldsValue["f1f8"]),
                "native_object_id": FieldsValue["f08"],
                "native_class": NodeValue.ClassValue.NameValue,
                "selected_by_f360": RootValue.FieldsValue["f360"] is NodeValue,
                "selected_by_f368": RootValue.FieldsValue["f368"] is NodeValue,
            }
        )
    return tuple(RowsValue)
