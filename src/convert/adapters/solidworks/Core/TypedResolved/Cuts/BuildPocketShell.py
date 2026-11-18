from dataclasses import replace as ReplaceValue

from convert.Geometry.Revolve.SweepModel import BuildSweepModel
from interchange.brep.Topology.BrepModel import BrepModel


# the inlet becomes an inner loop on the stock cap and the remaining cylindrical faces become inward cavity walls
def BuildPocketShell(
    StockValue: BrepModel,
    ToolValue: BrepModel,
    BodyId: str,
    PrefixValue: str,
    OpenCaps: tuple[int, ...],
) -> BrepModel:
    CapFaces = ToolValue.faces[0], ToolValue.faces[-1]
    Entrances = {IndexValue: CapFaces[IndexValue] for IndexValue in OpenCaps}
    RimLoops = {LoopId for Face in Entrances.values() for LoopId in Face.loop_ids}
    RimFaces = {Face.id for Face in Entrances.values()}
    RimSurfaces = {Face.surface_id for Face in Entrances.values()}
    Faces = tuple(
        (
            ReplaceValue(Face, loop_ids=(*Face.loop_ids, *Entrances[Index].loop_ids))
            if Index in Entrances
            else Face
        )
        for Index, Face in enumerate(StockValue.faces)
    ) + tuple(
        ReplaceValue(Face, same_sense=not Face.same_sense)
        for Face in ToolValue.faces
        if Face.id not in RimFaces
    )
    Loops = (
        *StockValue.loops,
        *(
            ReplaceValue(
                Loop,
                coedge_ids=Loop.coedge_ids[::-1],
                outer=Loop.outer and Loop.id not in RimLoops,
            )
            for Loop in ToolValue.loops
        ),
    )
    Uses = (
        *StockValue.coedges,
        *(ReplaceValue(Use, reversed=not Use.reversed) for Use in ToolValue.coedges),
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
        Uses,
    )
