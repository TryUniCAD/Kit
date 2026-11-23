from dataclasses import replace as ReplaceValue

from convert.Geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.Transform import KOriginZero


# the resident volume uses outward face traversals even when the portable face uses are reversed
def OrientPocket(ModelValue: BrepModel) -> BrepModel:
    ReversedFaces = {Value.face_id for Value in ModelValue.face_uses if Value.reversed}
    ReversedLoops = {
        LoopId
        for Value in ModelValue.faces
        if Value.id in ReversedFaces
        for LoopId in Value.loop_ids
    }
    ReversedUses = {
        UseId
        for Value in ModelValue.loops
        if Value.id in ReversedLoops
        for UseId in Value.coedge_ids
    }
    ReversedPlanes = {
        Value.surface_id
        for Value in ModelValue.faces
        if Value.same_sense == (Value.id in ReversedFaces)
    }
    return ReplaceValue(
        ModelValue,
        surfaces=tuple(
            (
                ReplaceValue(
                    Value, normal=OffsetVector(KOriginZero, Value.normal, -1.0)
                )
                if isinstance(Value, PlaneSurface) and Value.id in ReversedPlanes
                else Value
            )
            for Value in ModelValue.surfaces
        ),
        coedges=tuple(
            (
                ReplaceValue(Value, reversed=not Value.reversed)
                if Value.id in ReversedUses
                else Value
            )
            for Value in ModelValue.coedges
        ),
        loops=tuple(
            (
                ReplaceValue(Value, coedge_ids=Value.coedge_ids[::-1])
                if Value.id in ReversedLoops
                else Value
            )
            for Value in ModelValue.loops
        ),
        faces=tuple(ReplaceValue(Value, same_sense=True) for Value in ModelValue.faces),
        face_uses=tuple(
            ReplaceValue(Value, reversed=False) for Value in ModelValue.face_uses
        ),
    )
