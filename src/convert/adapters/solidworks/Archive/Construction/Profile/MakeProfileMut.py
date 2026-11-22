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
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginRef import (
    MakeOriginRef,
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
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


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
    GeometryValue = MakePolygon(InputValue, NodeValue)
    NodeValue.FieldsValue.update(
        MakeProfileData(GeometryValue.SketchValue, Reference, FrameValue)
    )
    return ProfileGraph(NodeValue, GeometryValue, Reference, FrameValue)
