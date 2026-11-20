from dataclasses import replace as ReplaceValue

from convert.Geometry.Revolve.SweepModel import BuildSweepModel
from interchange.brep.Topology.BrepModel import BrepModel


# the inlet becomes an inner loop on the stock cap and the remaining cylindrical faces become inward cavity walls
def MakePocketShell(
    StockValue: BrepModel,
    ToolValue: BrepModel,
    BodyId: str,
    PrefixValue: str,
    OpenCaps: tuple[int, ...],
) -> BrepModel:
    CapFaces = ToolValue.faces[0], ToolValue.faces[-1]
    Entrances = {IndexValue: CapFaces[IndexValue] for IndexValue in OpenCaps}
    RimLoops = {
        LoopId for FaceValue in Entrances.values() for LoopId in FaceValue.loop_ids
    }
    RimFaces = {FaceValue.id for FaceValue in Entrances.values()}
    RimSurfaces = {FaceValue.surface_id for FaceValue in Entrances.values()}
    Faces = tuple(
        (
            ReplaceValue(
                FaceValue, loop_ids=(*FaceValue.loop_ids, *Entrances[Index].loop_ids)
            )
            if Index in Entrances
            else FaceValue
        )
        for Index, FaceValue in enumerate(StockValue.faces)
    ) + tuple(
        ReplaceValue(FaceValue, same_sense=not FaceValue.same_sense)
        for FaceValue in ToolValue.faces
        if FaceValue.id not in RimFaces
    )
    Loops = (
        *StockValue.loops,
        *(
            ReplaceValue(
                LoopValue,
                coedge_ids=LoopValue.coedge_ids[::-1],
                outer=LoopValue.outer and LoopValue.id not in RimLoops,
            )
            for LoopValue in ToolValue.loops
        ),
    )
    Coedges = (
        *StockValue.coedges,
        *(
            ReplaceValue(Coedge, reversed=not Coedge.reversed)
            for Coedge in ToolValue.coedges
        ),
    )
    return BuildSweepModel(
        BodyId,
        PrefixValue,
        (*StockValue.curves, *ToolValue.curves),
        (
            *StockValue.surfaces,
            *(
                Surface
                for Surface in ToolValue.surfaces
                if Surface.id not in RimSurfaces
            ),
        ),
        (*StockValue.vertices, *ToolValue.vertices),
        (*StockValue.edges, *ToolValue.edges),
        Faces,
        Loops,
        Coedges,
    )
