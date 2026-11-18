from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
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
from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the drawing annotation cabinet must be its own registered empty model feature with actual containing model ownership
def MakeDrawCabinet(
    NameValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moDrawing_c")
    NodeValue = ArchiveNode(RuntimeClass("moDetailCabinet_c", 1), {})
    InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue, Allocator)
    NodeValue.FieldsValue.update(
        {
            "f35c": 0,
            "f368": EmptyRootRows(),
            "f370": 1.0,
            "f378": 1.0,
            "f388": EmptyRootRows(),
            "n3d8": 0,
            "f3d8": (),
            "f3f0": 0,
        }
    )
    ClearSystemMut(NodeValue)
    return NodeValue
