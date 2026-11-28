from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeCircle import (
    MakeCircle,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.BeginOffProf import (
    BeginOffProf,
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
    NodeValue, Reference = BeginOffProf(
        NameValue, OwnerValue, OffsetValue, TargetValue, Allocator
    )
    FrameValue = OffsetValue.FrameValue
    Geometry = MakeCircle(InputValue, NodeValue)
    NodeValue.FieldsValue.update(
        MakeProfileData(Geometry.SketchValue, Reference, FrameValue)
    )
    return ProfileGraph(NodeValue, Geometry, Reference, FrameValue)
