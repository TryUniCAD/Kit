from dataclasses import replace as ReplaceValue

from convert.Geometry.Revolve.SweepModel import BuildSweepModel
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepFace


# the generated stock and clipped sector must each carry one face on the common cylindrical wall
def ReadSweepWall(Model: BrepModel, Radius: float) -> tuple[BrepFace, CylinderSurface]:
    Walls = {
        Surface.id: Surface
        for Surface in Model.surfaces
        if isinstance(Surface, CylinderSurface) and Surface.radius == Radius
    }
    (Face,) = tuple(Face for Face in Model.faces if Face.surface_id in Walls)
    return Face, Walls[Face.surface_id]


# the cutter surface coinciding with the stock wall becomes an inner loop and the remaining tool faces bound the cavity
def OpenSweepWall(
    BodyId: str, Stock: BrepModel, Sector: BrepModel, Radius: float
) -> BrepModel:
    Wall, StockSurface = ReadSweepWall(Stock, Radius)
    Patch, SectorSurface = ReadSweepWall(Sector, Radius)
    if (
        StockSurface.axis != SectorSurface.axis
        or StockSurface.reference_direction != SectorSurface.reference_direction
        or Wall.same_sense != Patch.same_sense
        or len(Patch.loop_ids) != 1
    ):
        raise ValueError("cut sector does not open the stock wall")
    (OpeningId,) = Patch.loop_ids
    StockFaces = tuple(
        (
            ReplaceValue(Face, loop_ids=(*Face.loop_ids, OpeningId))
            if Face is Wall
            else Face
        )
        for Face in Stock.faces
    )
    CavityFaces = tuple(
        ReplaceValue(Face, same_sense=not Face.same_sense)
        for Face in Sector.faces
        if Face is not Patch
    )
    CavityLoops = tuple(
        ReplaceValue(
            Loop,
            coedge_ids=tuple(reversed(Loop.coedge_ids)),
            outer=Loop.id != OpeningId,
        )
        for Loop in Sector.loops
    )
    CavityCoedges = tuple(
        ReplaceValue(Coedge, reversed=not Coedge.reversed) for Coedge in Sector.coedges
    )
    return BuildSweepModel(
        BodyId,
        f"{BodyId}-sweep",
        Stock.curves + Sector.curves,
        Stock.surfaces
        + tuple(Surface for Surface in Sector.surfaces if Surface is not SectorSurface),
        Stock.vertices + Sector.vertices,
        Stock.edges + Sector.edges,
        StockFaces + CavityFaces,
        Stock.loops + CavityLoops,
        Stock.coedges + CavityCoedges,
    )
