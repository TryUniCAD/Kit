from math import dist as Distance

from convert.Geometry.Parasolid import LinePoint
from convert.Geometry.Revolve.SweepVector import DotVector, OffsetVector
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.JoinChmfEdge import (
    CoordsChmf,
)
from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.VectorSpace import SpaceVector


# each native line trim must actually arrive at the two endpoints of its oriented use
def CheckWarmLines(Actual: BrepModel) -> None:
    Curves = {
        Value.id: Value for Value in Actual.curves if isinstance(Value, LineCurve)
    }
    Points = {Value.id: Value.point for Value in Actual.vertices}
    if len(Curves) != len(Actual.edges) or len(Curves) != len(Actual.curves):
        raise ValueError("saved chamfer does not own one native line per trim")
    if len({Value.curve_id for Value in Actual.edges}) != len(Curves):
        raise ValueError("saved chamfer trim has a shared or detached line")
    for EdgeValue in Actual.edges:
        Curve = Curves[EdgeValue.curve_id]
        EndValues = (
            (EdgeValue.start_parameter, Points[EdgeValue.start_vertex_id]),
            (EdgeValue.end_parameter, Points[EdgeValue.end_vertex_id]),
        )
        if EdgeValue.degenerate or any(
            Distance(CoordsChmf(LinePoint(Curve, Parameter)), CoordsChmf(Point)) > 1e-8
            for Parameter, Point in EndValues
        ):
            raise ValueError("saved chamfer trim differs from its actual native line")


# the physical rings must lie on their own plane carriers independently of their outward traversal
def CheckWarmPlanes(
    Actual: BrepModel,
    RingsValue: tuple[tuple[SpaceVector, ...], ...],
) -> None:
    Faces = {Value.id: Value for Value in Actual.faces}
    Planes = {
        Value.id: Value for Value in Actual.surfaces if isinstance(Value, PlaneSurface)
    }
    if (
        len(Planes) != len(Faces)
        or len(Planes) != len(Actual.surfaces)
        or {FaceValue.surface_id for FaceValue in Faces.values()} != set(Planes)
        or not all(Value.outer for Value in Actual.loops)
        or any(len(FaceValue.loop_ids) != 1 for FaceValue in Faces.values())
        or Actual.pcurves
        or Actual.wires
    ):
        raise ValueError(
            "saved chamfer does not own one planar carrier and outer ring per face"
        )
    for UseValue, RingValue in zip(Actual.face_uses, RingsValue, strict=True):
        Plane = Planes[Faces[UseValue.face_id].surface_id]
        if any(
            abs(DotVector(OffsetVector(Point, Plane.origin, -1.0), Plane.normal)) > 1e-8
            for Point in RingValue
        ):
            raise ValueError(
                "saved chamfer native plane does not contain its actual trim"
            )
