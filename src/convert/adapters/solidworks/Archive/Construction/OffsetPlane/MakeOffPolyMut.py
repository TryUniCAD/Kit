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
from convert.adapters.solidworks.Archive.Construction.Sketch.MakePolygon import (
    MakePolygon,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import (
    PolygonInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a local polygon attaches to its own offset plane before any dimension owners are allocated
def MakeOffPolyMut(
    NameValue: str,
    InputValue: PolygonInput,
    OwnerValue: ArchiveNode,
    OffsetValue: OffsetGraph,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ProfileGraph:
    NodeValue, Reference = BeginOffProf(
        NameValue, OwnerValue, OffsetValue, TargetValue, Allocator
    )
    FrameValue = OffsetValue.FrameValue
    Geometry = MakePolygon(InputValue, NodeValue)
    NodeValue.FieldsValue.update(
        MakeProfileData(Geometry.SketchValue, Reference, FrameValue)
    )
    return ProfileGraph(NodeValue, Geometry, Reference, FrameValue)
