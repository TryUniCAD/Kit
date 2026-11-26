from convert.adapters.Fusion.Native.Cuts.IsCutRing import IsCutRing
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Planar.FaceBoundary import FaceBoundary
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadVertexPoint import (
    ReadVertexPoint,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.VectorMath import (
    CrossProduct,
    Normalize,
    Subtract,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# every native face must equal one generated boundary with the same physical outward normal
def CheckCutFace(
    Table: LiveTable,
    FaceValue: FaceBoundary,
    Expected: tuple[tuple[KJournalVector, ...], ...],
) -> int:
    Actual = tuple(
        ReadVertexPoint(Table, UseValue.StartVertex)
        for UseValue in FaceValue.BoundaryUses
    )
    Matches = tuple(
        Index
        for Index, RingValue in enumerate(Expected)
        if IsCutRing(Actual, RingValue)
    )
    if len(Matches) != 1:
        raise ValueError(
            "Native cut face does not match its generated parametric boundary"
        )
    RingValue = Expected[Matches[0]]
    Normal = Normalize(
        CrossProduct(
            Subtract(RingValue[1], RingValue[0]), Subtract(RingValue[2], RingValue[1])
        )
    )
    SavedNormal = Normalize(FaceValue.Surface.Normal)
    SameNumbers(
        tuple(-Value if FaceValue.Reversed else Value for Value in SavedNormal), Normal
    )
    if FaceValue.Surface.ReversedV:
        raise ValueError("Native cut planar carrier uses an unsupported reversed frame")
    return Matches[0]
