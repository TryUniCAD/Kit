from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# configuration progress must record the actual final allocator counter rather than a saved feature count or per case offset
def SetCfgStampMut(NodeValue: ArchiveNode, Allocator: PersistentIds) -> None:
    RequireRootNode(NodeValue, "moPartConfiguration_c")
    if Allocator.NextValue < 1:
        raise ValueError("configuration progress requires an allocated owning model")
    NodeValue.FieldsValue["f85c"] = Allocator.NextValue - 1
