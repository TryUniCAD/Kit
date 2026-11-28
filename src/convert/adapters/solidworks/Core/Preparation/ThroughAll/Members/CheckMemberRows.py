from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
    ReadNodeName,
    ReadRows,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceTree import (
    ReadSourceTree,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from interchange.document.Models.DocumentModel import CadDocument


# linked member identity and order must agree with the complete retained source observation
def CheckMemberRows(
    DocumentValue: CadDocument,
    ParentValue: ArchiveNode,
    NodesValue: tuple[ArchiveNode, ...],
) -> None:
    ParentId = "sldprt:feature:" + str(NativeNodeId(ParentValue))
    RowsValue = tuple(
        EntryValue
        for EntryValue in ReadRows(ReadSourceTree(DocumentValue).get("rows"))
        if EntryValue.get("parent_id") == ParentId
    )
    if tuple(
        FieldInt(EntryValue, "native_object_id") for EntryValue in RowsValue
    ) != tuple(NativeNodeId(NodeValue) for NodeValue in NodesValue):
        raise ValueError(
            "source member identity or order differs from its actual owner"
        )
    for EntryValue, NodeValue in zip(RowsValue, NodesValue, strict=True):
        if FieldText(
            EntryValue, "class"
        ) != NodeValue.ClassValue.NameValue or FieldText(
            EntryValue, "name"
        ) != ReadNodeName(
            NodeValue
        ):
            raise ValueError(
                "source member class or caption differs from retained presentation"
            )
