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
    (FaceValue,) = tuple(
        FaceValue for FaceValue in Model.faces if FaceValue.surface_id in Walls
    )
    return FaceValue, Walls[FaceValue.surface_id]


# the cutter surface coinciding with the stock wall becomes an inner loop and the remaining tool faces bound the cavity
def OpenSweepWall(
    BodyId: str, Stock: BrepModel, Sector: BrepModel, Radius: float
) -> BrepModel:
    StockWall, StockSurface = ReadSweepWall(Stock, Radius)
    Patch, SectorSurface = ReadSweepWall(Sector, Radius)
    if (
        StockSurface.axis != SectorSurface.axis
        or StockSurface.reference_direction != SectorSurface.reference_direction
        or StockWall.same_sense != Patch.same_sense
        or len(Patch.loop_ids) != 1
    ):
        raise ValueError("cut sector does not open the stock wall")
    (OpeningId,) = Patch.loop_ids
    StockFaces = tuple(
        (
            ReplaceValue(FaceValue, loop_ids=(*FaceValue.loop_ids, OpeningId))
            if FaceValue is StockWall
            else FaceValue
        )
        for FaceValue in Stock.faces
    )
    CavityFaces = tuple(
        ReplaceValue(FaceValue, same_sense=not FaceValue.same_sense)
        for FaceValue in Sector.faces
        if FaceValue is not Patch
    )
    CavityLoops = tuple(
        ReplaceValue(
            LoopValue,
            coedge_ids=tuple(reversed(LoopValue.coedge_ids)),
            outer=LoopValue.id != OpeningId,
        )
        for LoopValue in Sector.loops
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
