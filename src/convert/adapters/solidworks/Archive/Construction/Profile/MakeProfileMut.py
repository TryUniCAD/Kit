from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Profile.BeginProfileMut import (
    BeginProfileMut,
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


# an ordinary local profile must own a fresh wrapper and generated polygon while retaining its actual registered support datum
def MakeProfileMut(
    NameValue: str,
    OwnerValue: ArchiveNode,
    PlaneValue: ArchiveNode,
    AxisValue: str,
    InputValue: PolygonInput,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ProfileGraph:
    if type(InputValue) is not PolygonInput:
        raise TypeError("ordinary profile requires validated neutral polygon geometry")
    NodeValue, Reference, FrameValue = BeginProfileMut(
        NameValue, OwnerValue, PlaneValue, AxisValue, TargetValue, Allocator
    )
    GeometryValue = MakePolygon(InputValue, NodeValue)
    NodeValue.FieldsValue.update(
        MakeProfileData(GeometryValue.SketchValue, Reference, FrameValue)
    )
    return ProfileGraph(NodeValue, GeometryValue, Reference, FrameValue)
