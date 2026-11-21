from math import hypot as Hypot

from convert.Geometry.Revolve.SweepVector import CrossVector
from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepTopology import (
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepLoop,
)
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# cap and wall edge uses close outward with one opposite use on every shared edge
def BuildPrismFaces(
    Prefix: str,
    FrameValue: Transform,
    Curves: tuple[LineCurve, ...],
    Edges: tuple[BrepEdge, ...],
) -> tuple[
    tuple[PlaneSurface, ...],
    tuple[BrepFace, ...],
    tuple[BrepLoop, ...],
    tuple[BrepCoedge, ...],
]:
    Count = len(Edges) // 3
    AxisZ = FrameValue.z_axis
    LowerNormal = SpaceVector(-AxisZ.x, -AxisZ.y, -AxisZ.z)
    Specs = [
        (
            Curves[0].origin,
            LowerNormal,
            FrameValue.x_axis,
            tuple((Index, True) for Index in reversed(range(Count))),
        ),
        (
            Curves[Count].origin,
            AxisZ,
            FrameValue.x_axis,
            tuple((Count + Index, False) for Index in range(Count)),
        ),
    ]
    for Index, Curve in enumerate(Curves[:Count]):
        Following = (Index + 1) % Count
        Normal = CrossVector(Curve.direction, Curves[2 * Count + Index].direction)
        Length = Hypot(Normal.x, Normal.y, Normal.z)
        if Length == 0:
            raise ValueError("Extrude prism wall has a degenerate normal")
        Specs.append(
            (
                Curve.origin,
                SpaceVector(Normal.x / Length, Normal.y / Length, Normal.z / Length),
                Curve.direction,
                (
                    (Index, False),
                    (2 * Count + Following, False),
                    (Count + Index, True),
                    (2 * Count + Index, True),
                ),
            )
        )
    Surfaces: list[PlaneSurface] = []
    Faces: list[BrepFace] = []
    Loops: list[BrepLoop] = []
    Coedges: list[BrepCoedge] = []
    for Index, (Origin, Normal, Reference, EdgeUses) in enumerate(Specs):
        SurfaceId = f"{Prefix}-surface-{Index}"
        LoopId = f"{Prefix}-loop-{Index}"
        CoUses = tuple(
            BrepCoedge(f"{LoopId}-use-{Offset}", Edges[EdgeIndex].id, reversed=Reverse)
            for Offset, (EdgeIndex, Reverse) in enumerate(EdgeUses)
        )
        Surfaces.append(PlaneSurface(SurfaceId, Origin, Normal, Reference))
        Faces.append(BrepFace(f"{Prefix}-face-{Index}", SurfaceId, (LoopId,)))
        Loops.append(
            BrepLoop(LoopId, tuple(UseValue.id for UseValue in CoUses), outer=True)
        )
        Coedges.extend(CoUses)
    return tuple(Surfaces), tuple(Faces), tuple(Loops), tuple(Coedges)
