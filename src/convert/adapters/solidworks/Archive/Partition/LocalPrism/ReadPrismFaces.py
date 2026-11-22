from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismFaceLoop import (
    PrismFaceLoop,
)
from convert.Geometry.Parasolid import BrepTopology
from interchange.brep.Topology.BrepModel import BrepModel


# local ownership preserves the actual shell face order and only complete outer loops
def ReadPrismFaces(
    ModelValue: BrepModel, TopologyValue: BrepTopology
) -> tuple[PrismFaceLoop, ...]:
    if (
        tuple(UseValue.face_id for UseValue in ModelValue.face_uses)
        != tuple(FaceValue.id for FaceValue in ModelValue.faces)
        or ModelValue.shells[0].face_use_ids
        != tuple(UseValue.id for UseValue in ModelValue.face_uses)
        or len(ModelValue.faces) != len(ModelValue.loops)
    ):
        raise ValueError("local prism requires one ordered outer loop per shell face")
    Values: list[PrismFaceLoop] = []
    for FaceValue in ModelValue.faces:
        if not FaceValue.same_sense or len(FaceValue.loop_ids) != 1:
            raise ValueError("local prism requires an outward face with one loop")
        LoopValue = TopologyValue.loops[FaceValue.loop_ids[0]]
        UsesValue = tuple(
            TopologyValue.coedges[UseId] for UseId in LoopValue.coedge_ids
        )
        if (
            not LoopValue.outer
            or len(UsesValue) < 3
            or any(UseValue.pcurve_id for UseValue in UsesValue)
        ):
            raise ValueError("local prism requires one complete planar outer trim")
        Values.append(PrismFaceLoop(FaceValue, LoopValue, UsesValue))
    return tuple(Values)
