from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
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
from convert.adapters.solidworks.Archive.Construction.Profile.BeginProfileMut import (
    BeginProfileMut,
)
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileData import (
    MakeProfileData,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a circle feature uses the same owned plane frame registration and serialized profile as an ordinary polygon
def MakeCircleFeat(
    NameValue: str,
    OwnerValue: ArchiveNode,
    PlaneValue: ArchiveNode,
    AxisValue: str,
    InputValue: CircleInput,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ProfileGraph:
    if type(CastValue(object, InputValue)) is not CircleInput:
        raise TypeError("ordinary circle profile requires a validated circle")
    NodeValue, Reference, FrameValue = BeginProfileMut(
        NameValue, OwnerValue, PlaneValue, AxisValue, TargetValue, Allocator
    )
    GeometryValue = MakeCircle(InputValue, NodeValue)
    NodeValue.FieldsValue.update(
        MakeProfileData(GeometryValue.SketchValue, Reference, FrameValue)
    )
    return ProfileGraph(NodeValue, GeometryValue, Reference, FrameValue)
