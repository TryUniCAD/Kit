from convert.Geometry.Parasolid import BrepTopology
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadFaceRing import (
    PrismFinEnd,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadPrismFaces import (
    ReadPrismTrims,
)
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel


# each oriented ring must lie exactly on the axis plane carried by its own face
def CheckBoxPlanes(ModelValue: BrepModel) -> None:
    TopologyValue = BrepTopology(ModelValue)
    AxesValue = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    GroupsValue: set[tuple[int, float]] = set()
    for FaceValue in ModelValue.faces:
        (BoundaryValue,) = ReadPrismTrims(FaceValue, TopologyValue)
        PlaneValue = TopologyValue.surface_by_id[FaceValue.surface_id]
        if not isinstance(PlaneValue, PlaneSurface):
            raise ValueError("local solid requires plane carriers")
        Normal = PlaneValue.normal
        Direction = (abs(Normal.x), abs(Normal.y), abs(Normal.z))
        if Direction not in AxesValue:
            raise ValueError("local solid requires exact axis-plane normals")
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
            raise ValueError("local solid plane does not match its exact face station")
        GroupsValue.add((AxisIndex, Station))
    if len(GroupsValue) != len(ModelValue.faces):
        raise ValueError("local solid requires distinct face planes")
