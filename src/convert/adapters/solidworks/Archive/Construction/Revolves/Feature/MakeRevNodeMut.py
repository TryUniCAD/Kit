from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
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


# a revolution must allocate its concrete body feature class before applying the shared fresh feature and empty atom state
def MakeRevNodeMut(
    NameValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
    *,
    IsThin: bool = False,
    IsCut: bool = False,
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moPart_c")
    if IsCut and IsThin:
        raise ValueError("thin and stock-selected revolve construction are distinct")
    ClassName = "moRevolutionThin_c" if IsThin else "moRevolution_c"
    if IsCut:
        ClassName = "moRevCut_c"
    NodeValue = ArchiveNode(RuntimeClass(ClassName, 1), {})
    InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue, Allocator)
    NodeValue.FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    NodeValue.FieldsValue.update({FieldName: [] for FieldName in KAtomLists})
    NodeValue.FieldsValue.update(
        {
            "f35c": 0,
            "f368": {"n": 0, "items": []},
            "f388": {"n": 0, "items": []},
            "f538": None,
            "f4a0": 1,
            "f6e0": None,
            "f758": None,
            "f780": {"n": 0, "items": []},
            "f7a0": 0,
        }
    )
    return NodeValue
