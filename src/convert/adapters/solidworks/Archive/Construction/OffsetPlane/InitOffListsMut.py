from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the bounded offset model can retain initial null storage only for three independently empty lists
def InitOffListsMut(RootValue: ArchiveNode) -> None:
    FieldNames = ("f9d8", "fa48", "fa50")
    NodesValue = tuple(
        ArchiveNode.RequireNode(RootValue.FieldsValue[NameValue])
        for NameValue in FieldNames
    )
    if len(set(NodesValue)) != len(FieldNames) or any(
        NodeValue.ClassValue != RuntimeClass("suObList", 1)
        or NodeValue.FieldsValue != EmptyRootRows()
        for NodeValue in NodesValue
    ):
        raise ValueError("offset datum requires independent empty initial model lists")
    RootValue.FieldsValue.update(dict.fromkeys(FieldNames))
