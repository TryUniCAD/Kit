from dataclasses import replace as ReplaceValue

from convert.Geometry.Revolve.SweepModel import BuildSweepModel
from interchange.brep.Topology.BrepModel import BrepModel


# the inlet becomes an inner loop on the stock cap and the remaining cylindrical faces become inward cavity walls
def BuildPocketShell(
    StockValue: BrepModel, ToolValue: BrepModel, BodyId: str
) -> BrepModel:
    Entrance, *StockFaces = StockValue.faces
    Rim, *CavityFaces = ToolValue.faces
    (RimLoop,) = Rim.loop_ids
    Faces = (
        ReplaceValue(Entrance, loop_ids=(*Entrance.loop_ids, RimLoop)),
        *StockFaces,
        *(ReplaceValue(Face, same_sense=not Face.same_sense) for Face in CavityFaces),
    )
    Loops = (
        *StockValue.loops,
        *(
            ReplaceValue(
                Loop,
                coedge_ids=Loop.coedge_ids[::-1],
                outer=Loop.outer and Loop.id != RimLoop,
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
        f"{BodyId}-blind-pocket",
        (*StockValue.curves, *ToolValue.curves),
        (
            *StockValue.surfaces,
            *(
                Surface
                for Surface in ToolValue.surfaces
                if Surface.id != Rim.surface_id
            ),
        ),
        (*StockValue.vertices, *ToolValue.vertices),
        (*StockValue.edges, *ToolValue.edges),
        Faces,
        Loops,
        Uses,
    )
