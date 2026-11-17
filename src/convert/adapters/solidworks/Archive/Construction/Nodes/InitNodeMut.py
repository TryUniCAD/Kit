from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from typing import cast as CastValue


# generic constructor state must be created on the actual node before ownership and registration are modeled
def InitNodeMut(
    NodeValue: ArchiveNode,
    NameValue: str | None,
    Allocator: PersistentIds | None = None,
) -> None:
    if (
        not isinstance(CastValue(object, NodeValue), ArchiveNode)
        or not isinstance(NodeValue.ClassValue, RuntimeClass)
        or NodeValue.ClassValue.SchemaValue != 1
        or NodeValue.FieldsValue
    ):
        raise ValueError(
            "node initialization requires an empty concrete schema one archive node"
        )
    if NameValue is None:
        if Allocator is not None or NodeValue.ClassValue.NameValue != "moRefPlane_c":
            raise ValueError(
                "only unregistered reference planes may omit a native name"
            )
    elif type(NameValue) is not str or not NameValue or "\x00" in NameValue:
        raise ValueError("node names must be nonempty strings without null characters")
    if Allocator is not None and not isinstance(Allocator, PersistentIds):
        raise TypeError("node registration requires the shared persistent allocator")
    NameNode = (
        None
        if NameValue is None
        else ArchiveNode(RuntimeClass("moNodeName_c", 1), {"f08": NameValue})
    )
    NodeValue.FieldsValue.update(
        {"f18": NameNode, "f0c": 1, "f28": 0x40000000, "f08": -1, "f2c": 0, "f20": ""}
    )
    if Allocator is not None:
        _ = Allocator.AllocateMut(NodeValue)
