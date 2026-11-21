from collections.abc import Mapping

from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepFace


# a face carrier must be compared on the same trim rather than by name or surface order
def ReadFaceRims(
    ModelValue: BrepModel, EdgeIds: Mapping[str, str]
) -> dict[frozenset[str], BrepFace]:
    LoopsValue = {LoopValue.id: LoopValue for LoopValue in ModelValue.loops}
    Coedges = {Coedge.id: Coedge for Coedge in ModelValue.coedges}
    return {
        frozenset(
            EdgeIds[Coedges[CoedgeId].edge_id]
            for CoedgeId in LoopsValue[LoopId].coedge_ids
        ): FaceValue
        for FaceValue in ModelValue.faces
        for LoopId in FaceValue.loop_ids
    }
