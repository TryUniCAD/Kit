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
from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Construction.System.MakeDefaultData import (
    MakeDefaultData,
)
from convert.adapters.solidworks.Archive.Construction.System.MakeSystemNode import (
    MakeSystemNode,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# registered principal planes reuse native atom ownership and compute data from canonical frames rather than inline mate plane shortcuts
def MakePrincipal(
    AxisValue: str,
    NameValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
    PlaneFlags: bool,
) -> ArchiveNode:
    FrameValue = PrincipalFrame(AxisValue)
    if type(PlaneFlags) is not bool:
        raise TypeError("principal construction state requires an explicit boolean")
    NodeValue = MakeSystemNode(
        "moRefPlane_c", NameValue, OwnerValue, TargetValue, Allocator
    )
    FieldsValue = NodeValue.FieldsValue
    FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    FieldsValue.update({FieldName: [] for FieldName in KAtomLists})
    FieldsValue.update(
        {
            "f368": {"n": 0, "items": []},
            "f388": {"n": 0, "items": []},
            "f538": None,
            "f4a0": 1,
            "f6c0": dict.fromkeys(("x", "y", "z"), 0.0),
            "f6dc": 1 | (4 if PlaneFlags else 0),
            "f6e0": 0,
            "f6e8": None,
            "f6f0": 0,
            "f6f8": MakeDefaultData(AxisValue, FrameValue),
        }
    )
    ClearSystemMut(NodeValue)
    return NodeValue
