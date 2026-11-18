from convert.adapters.solidworks.Archive.Construction.Assembly.System.MakeAsmNode import (
    MakeAsmNode,
)
from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.MakeDefaultData import (
    MakeDefaultData,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# ordinary assembly principal planes use the same independently derived canonical geometry while retaining their actual assembly model feature ownership
def MakeAsmPlane(
    AxisValue: str,
    NameValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ArchiveNode:
    FrameValue = PrincipalFrame(AxisValue)
    NodeValue = MakeAsmNode(
        "moRefPlane_c", NameValue, OwnerValue, TargetValue, Allocator
    )
    FieldsValue = NodeValue.FieldsValue
    FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    FieldsValue.update({FieldName: [] for FieldName in KAtomLists})
    FieldsValue.update(
        {
            "f368": EmptyRootRows(),
            "f388": EmptyRootRows(),
            "f538": None,
            "f4a0": 1,
            "f6c0": dict.fromkeys(("x", "y", "z"), 0.0),
            "f6dc": 5,
            "f6e0": 0,
            "f6e8": None,
            "f6f0": 0,
            "f6f8": MakeDefaultData(AxisValue, FrameValue),
        }
    )
    return NodeValue
