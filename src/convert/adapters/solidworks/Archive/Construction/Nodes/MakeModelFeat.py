from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.MakeFeature import (
    MakeFeature,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# model features retain the generic feature state plus their independent native model feature discriminator
def MakeModelFeat(
    ClassName: str,
    NameValue: str | None,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds | None = None,
) -> ArchiveNode:
    NodeValue = MakeFeature(ClassName, NameValue, OwnerValue, TargetValue, Allocator)
    NodeValue.FieldsValue["f35c"] = 0
    return NodeValue
