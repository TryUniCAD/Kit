from typing import Literal

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


# each extrusion uses its concrete runtime class and the common empty atom constructor
def MakeExtrusionNodeMut(
    ClassName: Literal["moExtrusion_c", "moICE_c"],
    NameValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moPart_c")
    NodeValue = ArchiveNode(RuntimeClass(ClassName, 1), {})
    InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue, Allocator)
    FieldsValue = NodeValue.FieldsValue
    FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    FieldsValue.update({FieldName: [] for FieldName in KAtomLists})
    FieldsValue.update(
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
