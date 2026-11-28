from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
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
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.MakeOffsetSup import (
    MakeOffsetSup,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetGraph import (
    OffsetGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# offset profiles share a single constructor for the actual local datum reference and frame
def BeginOffProf(
    NameValue: str,
    OwnerValue: ArchiveNode,
    OffsetValue: OffsetGraph,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> tuple[ArchiveNode, ArchiveNode]:
    Reference = MakeOffsetSup(OwnerValue, OffsetValue)
    NodeValue = ArchiveNode(RuntimeClass("moProfileFeature_c", 1), {})
    InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue, Allocator)
    NodeValue.FieldsValue.update(
        f35c=0,
        f3dc=0,
        pd_f110=None,
        pd_f78=Reference,
        pd_ff0=FrameXform(OffsetValue.FrameValue),
    )
    return NodeValue, Reference
