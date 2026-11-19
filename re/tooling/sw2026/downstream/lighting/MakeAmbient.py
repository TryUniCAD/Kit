from downstream.lighting.AmbientFields import (
    AmbientFields,
)
from downstream.lighting.AmbientInput import (
    AmbientInput,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import FeatureTime
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# an ambient member reuses the actual generic feature identity and owner while supplying its complete source proved concrete tail
def MakeAmbient(
    OwnerValue: ArchiveNode,
    InputValue: AmbientInput,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
    CreatedAt: int,
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moEnvFolder_c")
    if type(InputValue) is not AmbientInput:
        raise TypeError("ambient construction requires explicit typed lighting")
    TimeFields = FeatureTime(CreatedAt)
    NodeValue = ArchiveNode(RuntimeClass("moAmbientLight_c", 1), {})
    InitFeatureMut(
        NodeValue, InputValue.NameValue, OwnerValue, TargetValue, Allocator
    )
    NodeValue.FieldsValue.update(AmbientFields(InputValue))
    NodeValue.FieldsValue.update(TimeFields)
    return NodeValue
