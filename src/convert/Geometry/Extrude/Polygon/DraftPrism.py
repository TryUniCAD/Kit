from math import isfinite as IsFinite, pi as CirclePi, tan as Tangent

from convert.Geometry.Extrude.Polygon.DraftMass import DraftMass
from convert.Geometry.Extrude.Polygon.DraftMeasures import DraftMeasures
from convert.Geometry.Extrude.Polygon.PrismEdges import BuildPrismEdges
from convert.Geometry.Extrude.Polygon.PrismFaces import BuildPrismFaces
from convert.Geometry.Revolve.SweepModel import BuildSweepModel
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# independently offset caps generate every drafted wall edge plane and physical measure
def BuildDraft(
    BodyId: str, Width: float, Depth: float, Height: float, Angle: float
) -> tuple[BrepModel, DraftMass, BoundingBox]:
    if (
        not BodyId
        or not all(IsFinite(Value) for Value in (Width, Depth, Height, Angle))
        or min(Width, Depth, Height) <= 0
        or not -CirclePi / 2 < Angle < CirclePi / 2
    ):
        raise ValueError(
            "Drafted rectangle requires finite positive dimensions and bounded taper"
        )
    Offset = Height * Tangent(Angle)
    if min(Width + 2 * Offset, Depth + 2 * Offset) <= 0:
        raise ValueError("Drafted rectangle collapses before its terminal cap")
    Points = (
        PlaneVector(0, 0),
        PlaneVector(Width, 0),
        PlaneVector(Width, Depth),
        PlaneVector(0, Depth),
    )
    UpperPoints = (
        PlaneVector(-Offset, -Offset),
        PlaneVector(Width + Offset, -Offset),
        PlaneVector(Width + Offset, Depth + Offset),
        PlaneVector(-Offset, Depth + Offset),
    )
    Prefix = f"{BodyId}-draft"
    Vertices, Curves, Edges = BuildPrismEdges(
        Prefix, KTransformIdentity, Points, 0, Height, UpperPoints
    )
    Surfaces, Faces, Loops, Coedges = BuildPrismFaces(
        Prefix, KTransformIdentity, Curves, Edges
    )
    Geometry = BuildSweepModel(
        BodyId, Prefix, Curves, Surfaces, Vertices, Edges, Faces, Loops, Coedges
    )
    Bounds = BoundingBox(
        SpaceVector(min(0, -Offset), min(0, -Offset), 0),
        SpaceVector(max(Width, Width + Offset), max(Depth, Depth + Offset), Height),
    )
    return Geometry, DraftMeasures(Width, Depth, Height, Tangent(Angle)), Bounds
