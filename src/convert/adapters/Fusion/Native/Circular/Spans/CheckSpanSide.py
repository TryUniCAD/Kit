from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from math import hypot as Hypot
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


# cylindrical side carriers must retain their radius axis and outward orientation
def CheckSpanSide(
    Surface: ConeNode,
    FaceValue: FaceNode,
    Coedges: tuple[CoedgeNode, ...],
    Model: FrustumBody,
) -> None:
    Radius = Model.BottomRadius / 10
    Center = (Model.BasePoint[0] / 10, Model.BasePoint[1] / 10)
    if FaceValue.Reversed or len(Coedges) != 2:
        raise ValueError("Native circular span has an inverted or incomplete side")
    SameNumbers(Surface.OriginCm[:2], Center)
    SameNumbers(Surface.AxisVector[:2], (0.0, 0.0))
    SameNumbers(
        (
            abs(Surface.AxisVector[2]),
            Surface.MajorAxisCm[2],
            Hypot(*Surface.MajorAxisCm[:2]),
            Surface.EllipseRatio,
            Surface.SineAngle,
            Surface.CosineAngle,
            Surface.UScaleCm,
        ),
        (1.0, 0.0, Radius, 1.0, 0.0, 1.0, Radius),
    )
    if Surface.Reversed or any(
        Value is not None
        for Value in (
            Surface.EllipseLower,
            Surface.EllipseUpper,
            Surface.ULower,
            Surface.UUpper,
            Surface.VLower,
            Surface.VUpper,
        )
    ):
        raise ValueError("Native circular span has unsupported carrier bounds")
