from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.InitExplodeMut import (
    InitExplodeMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# an explicit empty assembly manager needs its own config identity without becoming a resolved root
def MakeAsmExploded(
    OwnerValue: ArchiveNode, TargetValue: FeatureTarget, Allocator: PersistentIds
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moAssembly_c")
    if (
        OwnerValue.FieldsValue.get("f1590") is not None
        or OwnerValue.FieldsValue.get("f1598") != 0
    ):
        raise ValueError("assembly exploded manager requires an empty placement owner")
    NodeValue = ArchiveNode(RuntimeClass("moExplViewManager_c", 1), {})
    InitExplodeMut(NodeValue, OwnerValue, TargetValue, Allocator)
    return NodeValue
