from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeCircle import (
    MakeCircle,
)
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
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileData import (
    MakeProfileData,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# offset sketch allocation reuses the ordinary profile records with a retained translated support
def MakeOffCircMut(
    NameValue: str,
    InputValue: CircleInput,
    OwnerValue: ArchiveNode,
    OffsetValue: OffsetGraph,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ProfileGraph:
    if InputValue.CenterValue != (0.0, 0.0):
        raise ValueError("offset circle requires its measured fixed local centre")
    Reference = MakeOffsetSup(OwnerValue, OffsetValue)
    FrameValue = OffsetValue.FrameValue
    NodeValue = ArchiveNode(RuntimeClass("moProfileFeature_c", 1), {})
    InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue, Allocator)
    NodeValue.FieldsValue.update(
        f35c=0, f3dc=0, pd_f110=None, pd_f78=Reference, pd_ff0=FrameXform(FrameValue)
    )
    Geometry = MakeCircle(InputValue, NodeValue)
    NodeValue.FieldsValue.update(
        MakeProfileData(Geometry.SketchValue, Reference, FrameValue)
    )
    return ProfileGraph(NodeValue, Geometry, Reference, FrameValue)
