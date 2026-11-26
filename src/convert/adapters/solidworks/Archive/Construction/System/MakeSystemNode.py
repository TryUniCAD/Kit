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
from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KSystemExtras,
    KSystemFolders,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# independently qualified system constructors share generic feature initialization while their concrete additions remain separately owned
def MakeSystemNode(
    ClassName: str,
    NameValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moPart_c")
    if ClassName not in KSystemFolders | KSystemExtras:
        raise ValueError(
            "fresh part system feature class is outside the classified construction profile"
        )
    NodeValue = ArchiveNode(RuntimeClass(ClassName, 1), {})
    InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue, Allocator)
    if ClassName in KSystemExtras:
        NodeValue.FieldsValue["f35c"] = 0
    return NodeValue
