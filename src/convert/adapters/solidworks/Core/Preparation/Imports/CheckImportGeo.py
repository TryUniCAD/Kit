from itertools import product as Cartesian

from convert.Geometry.Parasolid import BrepTopology
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.ReadCylShape import (
    ReadCylShape,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPrism import (
    MakeLocalPrism,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadFaceRing import (
    PrismFinEnd,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadPrismFaces import (
    ReadPrismFaces,
)
from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel


# the measured prism profile requires the exact eight corners of an axis aligned box
def HasBoxCorners(ModelValue: BrepModel) -> bool:
    if (
        len(ModelValue.faces) != 6
        or len(ModelValue.edges) != 12
        or len(ModelValue.vertices) != 8
        or any(type(Value) is not PlaneSurface for Value in ModelValue.surfaces)
        or any(type(Value) is not LineCurve for Value in ModelValue.curves)
    ):
        return False
    Corners = {
        (Value.point.x, Value.point.y, Value.point.z) for Value in ModelValue.vertices
    }
    Stations = tuple(set(AxisValue) for AxisValue in zip(*Corners, strict=True))
    return (
        len(Corners) == 8
        and all(len(AxisValue) == 2 for AxisValue in Stations)
        and Corners == set(Cartesian(*Stations))
    )


# each validated ring must lie exactly on the axis plane carried by its own face
def CheckBoxPlanes(ModelValue: BrepModel) -> None:
    TopologyValue = BrepTopology(ModelValue)
    AxesValue = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    GroupsValue: set[tuple[int, float]] = set()
    for BoundaryValue in ReadPrismFaces(ModelValue, TopologyValue):
        PlaneValue = TopologyValue.surface_by_id[BoundaryValue.FaceValue.surface_id]
        if not isinstance(PlaneValue, PlaneSurface):
            raise ValueError("local box requires plane carriers")
        Normal = PlaneValue.normal
        Direction = (abs(Normal.x), abs(Normal.y), abs(Normal.z))
        if Direction not in AxesValue:
            raise ValueError("local box requires exact axis-plane normals")
        AxisIndex = AxesValue.index(Direction)
        Origin = PlaneValue.origin
        Station = (Origin.x, Origin.y, Origin.z)[AxisIndex]
        PointsValue = (
            TopologyValue.vertex_by_id[PrismFinEnd(TopologyValue, UseValue)].point
            for UseValue in BoundaryValue.UsesValue
        )
        if {
            (PointValue.x, PointValue.y, PointValue.z)[AxisIndex]
            for PointValue in PointsValue
        } != {Station}:
            raise ValueError("local box plane does not match its exact face station")
        GroupsValue.add((AxisIndex, Station))
    if len(GroupsValue) != 6:
        raise ValueError("local box requires six distinct face planes")


# matching corners still require the shared compiler to prove the complete outward face and trim graph
def CheckImportGeo(ModelValue: BrepModel) -> None:
    if HasBoxCorners(ModelValue):
        _ = MakeLocalPrism(ModelValue)
        CheckBoxPlanes(ModelValue)
        return
    _ = ReadCylShape(ModelValue)
