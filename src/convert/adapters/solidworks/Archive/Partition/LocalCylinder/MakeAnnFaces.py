from convert.Geometry.Parasolid import BrepTopology
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.MakeCylRim import (
    MakeCylFin,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeBoundFace import (
    MakeBoundFace,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    PrismCell,
    PrismRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismChain import (
    PrismChain,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepFace


# every periodic loop owns one self closing fin and the actual opposite edge use
def MakeAnnLoops(
    FaceValue: BrepFace, TopologyValue: BrepTopology
) -> tuple[PrismCell, ...]:
    Values: list[PrismCell] = []
    FaceRef = PrismRef(14, FaceValue.id)
    RefsValue = tuple(PrismRef(15, LoopId) for LoopId in FaceValue.loop_ids)
    LinksValue = PrismChain(RefsValue)
    for LoopRef in RefsValue:
        LoopValue = TopologyValue.loops[LoopRef.IdValue]
        (UseId,) = LoopValue.coedge_ids
        UseValue = TopologyValue.coedges[UseId]
        EdgeRef = PrismRef(16, UseValue.edge_id)
        Opposite = next(
            Value
            for Value in TopologyValue.edge_coedges[EdgeRef.IdValue]
            if Value != UseId
        )
        Values.append(
            PrismCell(
                LoopRef,
                {
                    "face": FaceRef,
                    "halfedge": PrismRef(17, UseId),
                    "next": LinksValue[LoopRef][1],
                },
            )
        )
        Values.append(
            MakeCylFin(UseValue, TopologyValue.coedges[Opposite], LoopRef, EdgeRef)
        )
    return tuple(Values)


# both face sides must follow the ordered annular boundary with its individual surface sense
def MakeAnnFaces(
    ModelValue: BrepModel,
    TopologyValue: BrepTopology,
    SurfaceRefs: tuple[PrismRef, ...],
) -> tuple[PrismCell, ...]:
    FaceRefs = tuple(PrismRef(14, Value.id) for Value in ModelValue.faces)
    LinksValue = PrismChain(FaceRefs)
    return tuple(
        CellValue
        for FaceValue, FaceRef, SurfaceRef in zip(
            ModelValue.faces, FaceRefs, SurfaceRefs, strict=True
        )
        for CellValue in (
            MakeBoundFace(
                FaceRef,
                PrismRef(15, FaceValue.loop_ids[0]),
                SurfaceRef,
                *LinksValue[FaceRef],
                FaceValue.same_sense,
            ),
            *MakeAnnLoops(FaceValue, TopologyValue),
        )
    )
