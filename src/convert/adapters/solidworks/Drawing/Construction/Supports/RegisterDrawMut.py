from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# shared support factories publish the expected identifier before the owning drawing registers that exact constructed node
def RegisterDrawMut(NodeValue: ArchiveNode, Allocator: PersistentIds) -> None:
    if (
        type(NodeValue.FieldsValue.get("f08")) is not int
        or NodeValue.FieldsValue["f08"] != Allocator.NextValue
    ):
        raise ValueError(
            "drawing support identifier differs from its actual next allocation"
        )
    NodeValue.FieldsValue["f08"] = -1
    _ = Allocator.AllocateMut(NodeValue)
