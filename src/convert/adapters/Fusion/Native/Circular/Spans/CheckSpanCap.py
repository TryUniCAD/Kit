from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from math import hypot as Hypot
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


# physical end stations determine cap orientation independently of saved carrier direction
def CheckSpanCap(
    Surface: PlaneNode,
    FaceValue: FaceNode,
    Coedges: tuple[CoedgeNode, ...],
    Model: FrustumBody,
) -> float:
    Center = (Model.BasePoint[0] / 10, Model.BasePoint[1] / 10)
    Lower = Model.BasePoint[2] / 10
    Upper = Lower + Model.Height / 10
    Level = (
        Lower
        if abs(Lower - Surface.OriginCm[2]) <= abs(Upper - Surface.OriginCm[2])
        else Upper
    )
    SameNumbers(Surface.OriginCm, (*Center, Level))
    SameNumbers(Surface.Normal[:2], (0.0, 0.0))
    SameNumbers(
        (
            abs(Surface.Normal[2]),
            Surface.ReferenceAxis[2],
            Hypot(*Surface.ReferenceAxis[:2]),
        ),
        (1.0, 0.0, 1.0),
    )
    Outward = Surface.Normal[2] * (-1 if FaceValue.Reversed else 1)
    SameNumbers((Outward,), (-1.0 if Level == Lower else 1.0,))
    if (
        len(Coedges) != 1
        or Surface.ReversedV
        or any(
            Value is not None
            for Value in (
                Surface.ULower,
                Surface.UUpper,
                Surface.VLower,
                Surface.VUpper,
            )
        )
    ):
        raise ValueError("Native circular cap has unsupported boundary framing")

    return Level
