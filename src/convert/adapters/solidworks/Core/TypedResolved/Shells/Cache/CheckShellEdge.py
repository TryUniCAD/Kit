from convert.Geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Topology.BrepModel import BrepModel


# each straight saved edge interval must end at its actual shell vertices
def CheckShellEdge(ModelValue: BrepModel, BoundValue: float) -> None:
    Curves = {Value.id: Value for Value in ModelValue.curves}
    Points = {Value.id: Value.point for Value in ModelValue.vertices}
    if set(Curves) != {Value.curve_id for Value in ModelValue.edges}:
        raise ValueError("SOLIDWORKS shell has unrelated saved line carriers")
    for EdgeValue in ModelValue.edges:
        Curve = Curves[EdgeValue.curve_id]
        if not isinstance(Curve, LineCurve) or EdgeValue.degenerate:
            raise ValueError("SOLIDWORKS shell has an unsupported saved edge")
        for ParamValue, VertexId in (
            (EdgeValue.start_parameter, EdgeValue.start_vertex_id),
            (EdgeValue.end_parameter, EdgeValue.end_vertex_id),
        ):
            Expected = OffsetVector(Curve.origin, Curve.direction, ParamValue)
            Actual = Points[VertexId]
            if (
                max(
                    abs(Expected.x - Actual.x),
                    abs(Expected.y - Actual.y),
                    abs(Expected.z - Actual.z),
                )
                > BoundValue
            ):
                raise ValueError(
                    "SOLIDWORKS shell saved line differs from its linked vertices"
                )
