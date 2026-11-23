from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismFaceLoop import (
    PrismFaceLoop,
)
from convert.Geometry.Parasolid import BrepTopology
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepFace


# ordered trims keep the first boundary outward and any secondary boundary inward
def ReadPrismTrims(
    FaceValue: BrepFace, TopologyValue: BrepTopology
) -> tuple[PrismFaceLoop, ...]:
    Values: list[PrismFaceLoop] = []
    for IndexValue, LoopId in enumerate(FaceValue.loop_ids):
        LoopValue = TopologyValue.loops[LoopId]
        UsesValue = tuple(
            TopologyValue.coedges[UseId] for UseId in LoopValue.coedge_ids
        )
        if (
            LoopValue.outer != (IndexValue == 0)
            or len(UsesValue) < 3
            or any(UseValue.pcurve_id for UseValue in UsesValue)
        ):
            raise ValueError("local prism requires complete ordered planar trims")
        Values.append(PrismFaceLoop(FaceValue, LoopValue, UsesValue))
    return tuple(Values)


# local ownership follows shell face order and allows additional trims only for a qualified pocket
def ReadPrismFaces(
    ModelValue: BrepModel, TopologyValue: BrepTopology, *, AllowPocket: bool = False
) -> tuple[PrismFaceLoop, ...]:
    if (
        tuple(UseValue.face_id for UseValue in ModelValue.face_uses)
        != tuple(FaceValue.id for FaceValue in ModelValue.faces)
        or ModelValue.shells[0].face_use_ids
        != tuple(UseValue.id for UseValue in ModelValue.face_uses)
        or len(ModelValue.loops) != len(ModelValue.faces) + int(AllowPocket)
    ):
        raise ValueError("local prism requires one ordered outer loop per shell face")
    Values: list[PrismFaceLoop] = []
    for FaceValue in ModelValue.faces:
        if not FaceValue.same_sense or not 1 <= len(FaceValue.loop_ids) <= 1 + int(
            AllowPocket
        ):
            raise ValueError("local prism requires an outward face with one loop")
        Values.extend(ReadPrismTrims(FaceValue, TopologyValue))
    if (
        len(Values) != len(ModelValue.loops)
        or {BoundaryValue.LoopValue.id for BoundaryValue in Values}
        != TopologyValue.loops.keys()
    ):
        raise ValueError("local prism requires one face owner for each loop")
    return tuple(Values)
