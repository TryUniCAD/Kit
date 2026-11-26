from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Construction.System.MakeSystemNode import (
    MakeSystemNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the empty annotation cabinet remains an independent model feature with native unit scale and no annotation content
def MakeCabinet(
    NameValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ArchiveNode:
    NodeValue = MakeSystemNode(
        "moDetailCabinet_c", NameValue, OwnerValue, TargetValue, Allocator
    )
    NodeValue.FieldsValue.update(
        {
            "f368": {"n": 0, "items": []},
            "f370": 1.0,
            "f378": 1.0,
            "f388": {"n": 0, "items": []},
            "n3d8": 0,
            "f3d8": [],
            "f3f0": 0,
        }
    )
    ClearSystemMut(NodeValue)
    return NodeValue
