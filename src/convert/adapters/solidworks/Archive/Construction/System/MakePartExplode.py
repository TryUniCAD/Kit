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


# the part manager needs the actual empty configuration slot and shares its model persistent allocator
def MakePartExplode(
    OwnerValue: ArchiveNode, TargetValue: FeatureTarget, Allocator: PersistentIds
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moPart_c")
    FieldsValue = OwnerValue.FieldsValue
    FlagsValue = FieldsValue.get("f1400")
    if (
        "f13f8" not in FieldsValue
        or FieldsValue["f13f8"] is not None
        or type(FlagsValue) is not int
        or FlagsValue != 0
    ):
        raise ValueError("part exploded manager requires an empty configuration owner")
    OwnerId = Allocator.Allocations.get((OwnerValue, "f08"))
    if OwnerId is None or FieldsValue.get("f08") != OwnerId or Allocator.NextValue <= 0:
        raise ValueError(
            "part exploded manager requires its model persistent allocator"
        )
    NodeValue = ArchiveNode(RuntimeClass("moPrtExplViewManager_c", 1), {})
    InitExplodeMut(NodeValue, OwnerValue, TargetValue, Allocator)
    return NodeValue
