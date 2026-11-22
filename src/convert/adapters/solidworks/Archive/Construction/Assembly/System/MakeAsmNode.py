from convert.adapters.solidworks.Archive.Construction.Assembly.System.AsmVocabulary import (
    KAsmFolders,
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


# assembly system features initialize their actual concrete nodes without weakening the separate qualified part construction guards
def MakeAsmNode(
    ClassName: str,
    NameValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moAssembly_c")
    if ClassName not in (
        *KAsmFolders,
        "moDetailCabinet_c",
        "moRefPlane_c",
        "moOriginProfileFeature_c",
        "moMateGroup_c",
        "moReference_c",
    ):
        raise ValueError("unsupported ordinary assembly feature constructor")
    NodeValue = ArchiveNode(RuntimeClass(ClassName, 1), {})
    InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue, Allocator)
    if ClassName in (
        "moDetailCabinet_c",
        "moRefPlane_c",
        "moOriginProfileFeature_c",
        "moMateGroup_c",
    ):
        NodeValue.FieldsValue["f35c"] = 0
    return NodeValue
