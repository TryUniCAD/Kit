from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.LightFields import (
    LightFields,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeFeatTime import (
    MakeFeatTime,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# each authored light needs its actual environment and one freshly allocated persistent identity
def MakeLightMut(
    OwnerValue: ArchiveNode,
    InputValue: LightInput,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moEnvFolder_c")
    if type(InputValue) is not LightInput:
        raise TypeError("light construction requires typed semantic intent")
    ClassName = (
        "moAmbientLight_c"
        if InputValue.KindValue == "ambient"
        else "moDirectionLight_c"
    )
    NodeValue = ArchiveNode(RuntimeClass(ClassName, 1), {})
    InitFeatureMut(NodeValue, InputValue.NameValue, OwnerValue, TargetValue, Allocator)
    NodeValue.FieldsValue.update(LightFields(InputValue))
    NodeValue.FieldsValue.update(MakeFeatTime(InputValue.CreatedValue))
    return NodeValue
