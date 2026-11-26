from collections.abc import Callable

from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Header.ReadHeadItems import ReadHeadItems
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# configuration direct slots follow self then directory order without borrowing header indices
def HeaderRefNodes(
    HeaderValue: ArchiveNode,
    Version: int,
    ReadItems: Callable[[ArchiveNode], tuple[ArchiveNode, ...]] = ReadHeadItems,
) -> tuple[ArchiveNode, ...]:
    if Version != KHeaderVersion:
        raise ValueError(f"unsupported SOLIDWORKS direct header version {Version}")
    HeaderValue = ArchiveNode.RequireNode(HeaderValue)
    if HeaderValue.ClassValue != RuntimeClass("moHeader_c", 1):
        raise ValueError("SOLIDWORKS configuration requires a concrete model header")
    if not {"f38", "f30"} <= HeaderValue.FieldsValue.keys():
        raise ValueError("SOLIDWORKS direct header fields are incomplete")
    Owner = HeaderValue.FieldsValue["f38"]
    Directory = HeaderValue.FieldsValue["f30"]
    Items: tuple[ArchiveNode, ...] = ()
    if Directory is not None:
        Directory = ArchiveNode.RequireNode(Directory)
        if Directory.ClassValue != RuntimeClass("moExtObjectList_c", 1):
            raise ValueError("SOLIDWORKS direct header directory has the wrong class")
        Items = ReadItems(Directory)
    Nodes = tuple(
        ArchiveNode.RequireNode(NodeValue)
        for NodeValue in (() if Owner is None else (Owner,)) + Items
    )
    if any(
        NodeValue.ClassValue != RuntimeClass("moExtObject_c", 1) for NodeValue in Nodes
    ):
        raise ValueError("SOLIDWORKS direct header reference has the wrong class")
    return Nodes
