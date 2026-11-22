from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanRim import CheckSpanRim


# every closed boundary must have reciprocal uses with coherent physical winding
def CheckSpanUses(
    State: GeometryState,
    FaceValue: FaceNode,
    Coedges: tuple[CoedgeNode, ...],
    Surface: ConeNode | PlaneNode,
    Model: FrustumBody,
) -> None:
    Radius = Model.BottomRadius / 10
    Center = (Model.BasePoint[0] / 10, Model.BasePoint[1] / 10)
    Lower = Model.BasePoint[2] / 10
    Upper = Lower + Model.Height / 10
    for Coedge in Coedges:
        Partner = SnapEntity(State, Coedge.Partner, CoedgeNode)
        if (
            Partner.Partner != State.Entities.index(Coedge)
            or Partner.EdgeRef != Coedge.EdgeRef
            or Partner.Reversed == Coedge.Reversed
        ):
            raise ValueError("Native circular span boundary uses are not reciprocal")
        EdgeValue = SnapEntity(State, Coedge.EdgeRef, EdgeNode)
        Curve = SnapEntity(State, EdgeValue.CurveRef, EllipseNode)
        Level = (
            Lower
            if abs(Lower - Curve.OriginCm[2]) <= abs(Upper - Curve.OriginCm[2])
            else Upper
        )
        CheckSpanRim(State, EdgeValue, (*Center, Level), Radius)
        if isinstance(Surface, PlaneNode):
            SameNumbers((Curve.OriginCm[2],), (Surface.OriginCm[2],))
            Winding = (
                Curve.Normal[2]
                * (-1 if EdgeValue.Reversed else 1)
                * (-1 if Coedge.Reversed else 1)
            )
            SameNumbers(
                (Winding,), (Surface.Normal[2] * (-1 if FaceValue.Reversed else 1),)
            )
