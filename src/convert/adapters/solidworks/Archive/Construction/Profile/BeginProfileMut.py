from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
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
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginRef import (
    MakeOriginRef,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# local planar profiles share the registered feature frame and actual principal support before allocating their sketch topology
def BeginProfileMut(
    NameValue: str,
    OwnerValue: ArchiveNode,
    PlaneValue: ArchiveNode,
    AxisValue: str,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> tuple[ArchiveNode, ArchiveNode, PlaneFrame]:
    Reference = MakeOriginRef(PlaneValue, OwnerValue, AxisValue)
    FrameValue = PrincipalFrame(AxisValue)
    NodeValue = ArchiveNode(RuntimeClass("moProfileFeature_c", 1), {})
    InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue, Allocator)
    NodeValue.FieldsValue.update(
        {
            "f35c": 0,
            "f3dc": 0,
            "pd_f110": None,
            "pd_f78": Reference,
            "pd_ff0": FrameXform(FrameValue),
        }
    )
    return NodeValue, Reference, FrameValue
