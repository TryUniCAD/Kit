from convert.Geometry.Parasolid import BrepTopology
from convert.Geometry.Revolve.SweepInput import CheckSweepFrame
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckAnnEdges import (
    CheckAnnEdges,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckAnnFrame import (
    CheckAnnFrame,
    ReadAnnPlanes,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckAnnBores import (
    CheckAnnBores,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    PrismVector,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalXmtProfile import (
    KLocalLimit,
)
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel


# the bare model must account for one analytic annular boundary and its full topology
def CheckAnnSize(ModelValue: BrepModel, WallCount: int) -> None:
    FaceCount = WallCount + 2
    EdgeCount = 2 * WallCount
    LoopCount = 2 * EdgeCount
    if (
        14 * WallCount + 9 > KLocalLimit
        or tuple(
            len(Values)
            for Values in (
                ModelValue.bodies,
                ModelValue.regions,
                ModelValue.shells,
                ModelValue.shell_uses,
                ModelValue.faces,
                ModelValue.face_uses,
                ModelValue.surfaces,
                ModelValue.loops,
                ModelValue.coedges,
                ModelValue.edges,
                ModelValue.curves,
                ModelValue.vertices,
            )
        )
        != (
            1,
            1,
            1,
            1,
            FaceCount,
            FaceCount,
            FaceCount,
            LoopCount,
            LoopCount,
            EdgeCount,
            EdgeCount,
            EdgeCount,
        )
        or not ModelValue.regions[0].solid
        or not ModelValue.shells[0].closed
        or ModelValue.shell_uses[0].reversed
        or ModelValue.validate()
        or ModelValue.shells[0].face_use_ids
        != tuple(Value.id for Value in ModelValue.face_uses)
        or tuple(Value.face_id for Value in ModelValue.face_uses)
        != tuple(Value.id for Value in ModelValue.faces)
        or any(Value.reversed for Value in ModelValue.face_uses)
        or len({Value.surface_id for Value in ModelValue.faces}) != FaceCount
        or len({Value.curve_id for Value in ModelValue.edges}) != EdgeCount
        or len({Value.start_vertex_id for Value in ModelValue.edges}) != EdgeCount
        or len({LoopId for Value in ModelValue.faces for LoopId in Value.loop_ids})
        != LoopCount
    ):
        raise ValueError("local annulus requires one complete analytic solid boundary")


# the signed inside wall and cap normals must agree with the solid side of each face
def CheckAnnFaces(
    ModelValue: BrepModel,
    TopologyValue: BrepTopology,
    OuterValue: CylinderSurface,
    FarPlane: PlaneSurface,
    WallCount: int,
) -> None:
    for FaceValue in ModelValue.faces:
        Carrier = TopologyValue.surface_by_id[FaceValue.surface_id]
        if isinstance(Carrier, PlaneSurface):
            CheckSweepFrame(Carrier.origin, Carrier.normal, Carrier.reference_direction)
            SenseValue = 1 if FaceValue.same_sense else -1
            CapSign = 1 if Carrier is FarPlane else -1
            if len(FaceValue.loop_ids) != WallCount or tuple(
                SenseValue * Value for Value in PrismVector(Carrier.normal)
            ) != tuple(CapSign * Value for Value in PrismVector(OuterValue.axis)):
                raise ValueError(
                    "local annulus has inconsistent signed cap or rim geometry"
                )
        elif (
            not isinstance(Carrier, CylinderSurface)
            or FaceValue.same_sense != (Carrier is OuterValue)
            or tuple(TopologyValue.loops[LoopId].outer for LoopId in FaceValue.loop_ids)
            != (True, False)
        ):
            raise ValueError(
                "local annulus must preserve the opposing wall sense and its trims"
            )


# geometry admission must prove the shell and every circle from the supplied solid
def CheckAnnBrep(ModelValue: BrepModel, *, CheckSeams: bool = False) -> None:
    PlanesValue = tuple(
        Value for Value in ModelValue.surfaces if isinstance(Value, PlaneSurface)
    )
    WallsValue = sorted(
        (Value for Value in ModelValue.surfaces if isinstance(Value, CylinderSurface)),
        key=AnnWallRadius,
    )
    WallCount = len(WallsValue)
    CheckAnnSize(ModelValue, WallCount)
    if len(PlanesValue) != 2 or WallCount < 2:
        raise ValueError("local annulus requires two planes and cylindrical walls")
    TopologyValue = BrepTopology(ModelValue)
    *BoresValue, OuterWall = WallsValue
    NearPlane, FarPlane = (
        CheckAnnFrame(OuterWall, BoresValue[0], PlanesValue)
        if WallCount == 2
        else ReadAnnPlanes(OuterWall, PlanesValue)
    )
    CheckAnnFaces(ModelValue, TopologyValue, OuterWall, FarPlane, WallCount)
    RimValues = CheckAnnEdges(
        ModelValue, TopologyValue, OuterWall, WallCount, CheckSeams=CheckSeams
    )
    if WallCount > 2:
        CheckAnnBores(OuterWall, BoresValue, (NearPlane, FarPlane), RimValues)


# wall identity follows its actual radial ordering rather than face sequence
def AnnWallRadius(Value: CylinderSurface) -> float:
    return Value.radius
