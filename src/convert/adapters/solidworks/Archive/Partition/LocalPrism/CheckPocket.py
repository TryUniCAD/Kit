from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismRings import (
    PrismRings,
    RotatePrismRing,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PocketRings import (
    PocketRings,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismFaceLoop import (
    PrismFaceLoop,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    PrismVector,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadFaceRing import (
    KPrismRing,
)
from convert.Geometry.Parasolid import BrepTopology
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel


# each complete ring must lie on its actual carrier station along one axis
def CheckRimPlane(PlaneValue: object, RingValue: KPrismRing) -> None:
    if not isinstance(PlaneValue, PlaneSurface):
        raise ValueError("local pocket requires a plane for each rim and wall")
    AxisValue = tuple(map(abs, PrismVector(PlaneValue.normal)))
    if sorted(AxisValue) != [0.0, 0.0, 1.0]:
        raise ValueError("local pocket requires exact axis-plane normals")
    IndexValue = AxisValue.index(1.0)
    if {PointValue[IndexValue] for PointValue in RingValue} != {
        PrismVector(PlaneValue.origin)[IndexValue]
    }:
        raise ValueError("local pocket trim differs from its exact plane station")


# strict rectangular stations account for an exterior and one inset blind cavity
def WantPocketRings(
    Vertices: KPrismRing, InnerRing: KPrismRing
) -> tuple[tuple[KPrismRing, ...], ...]:
    LowerX, LowerY, LowerZ = map(min, zip(*Vertices, strict=True))
    UpperX, UpperY, UpperZ = map(max, zip(*Vertices, strict=True))
    InnerMinX, InnerMinY, _ = map(min, zip(*InnerRing, strict=True))
    InnerMaxX, InnerMaxY, _ = map(max, zip(*InnerRing, strict=True))
    Levels = sorted({Value[2] for Value in Vertices})
    if len(Levels) != 3 or not (
        LowerX < InnerMinX < InnerMaxX < UpperX
        and LowerY < InnerMinY < InnerMaxY < UpperY
    ):
        raise ValueError(
            "local pocket requires one finite rectangular recess inside the outer rim"
        )
    Floor, OuterRim, OuterWalls = PocketRings(
        (LowerX, LowerY, LowerZ), (UpperX, UpperY, UpperZ), Cavity=False
    )
    InnerFloor, InnerRim, InnerWalls = PocketRings(
        (InnerMinX, InnerMinY, Levels[1]), (InnerMaxX, InnerMaxY, UpperZ), Cavity=True
    )
    return (
        (Floor,),
        (OuterRim, InnerRim),
        (InnerFloor,),
        *((WallRing,) for WallRing in OuterWalls + InnerWalls),
    )


# the actual face groups must match the entire directed boundary and rim association
def CheckPocket(
    ModelValue: BrepModel,
    TopologyValue: BrepTopology,
    Boundaries: tuple[PrismFaceLoop, ...],
) -> None:
    if (
        len(ModelValue.faces),
        len(ModelValue.loops),
        len(ModelValue.edges),
        len(ModelValue.coedges),
        len(ModelValue.vertices),
    ) != (11, 12, 24, 48, 16):
        raise ValueError("local pocket has an unsupported face or boundary inventory")
    Rings = PrismRings(Boundaries, TopologyValue)
    ByFace: dict[str, list[KPrismRing]] = {}
    Inner: list[KPrismRing] = []
    for Boundary, RingValue in zip(Boundaries, Rings, strict=True):
        CheckRimPlane(
            TopologyValue.surface_by_id[Boundary.FaceValue.surface_id], RingValue
        )
        ByFace.setdefault(Boundary.FaceValue.id, []).append(RotatePrismRing(RingValue))
        if not Boundary.LoopValue.outer:
            Inner.append(RingValue)
    if len(Inner) != 1:
        raise ValueError("local pocket requires exactly one interior rim loop")
    Vertices = tuple(PrismVector(Value.point) for Value in ModelValue.vertices)
    Expected = WantPocketRings(Vertices, Inner[0])
    if sorted(tuple(Value) for Value in ByFace.values()) != sorted(
        tuple(map(RotatePrismRing, Value)) for Value in Expected
    ):
        raise ValueError(
            "local pocket boundary differs from the complete rectangular recess"
        )
