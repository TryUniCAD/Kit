from math import isclose as IsClose
from convert.Formats.Fusion.BrepCodec.Journal.Planar.FaceBoundary import FaceBoundary
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadVertexPoint import (
    ReadVertexPoint,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# cache coordinates must equal one authored tool rather than an unrelated saved body
def PickCacheShape(
    Table: LiveTable,
    Faces: tuple[FaceBoundary, ...],
    Expected: tuple[tuple[KJournalVector, ...], ...],
) -> int:
    Actual = {
        ReadVertexPoint(Table, UseValue.StartVertex)
        for FaceValue in Faces
        for UseValue in FaceValue.BoundaryUses
    }
    Matches = tuple(
        Index
        for Index, Points in enumerate(Expected)
        if len(Actual) == len(Points)
        and all(
            any(
                all(
                    IsClose(First, Second, rel_tol=1e-9, abs_tol=1e-9)
                    for First, Second in zip(Point, Other, strict=True)
                )
                for Other in Points
            )
            for Point in Actual
        )
    )
    if len(Matches) != 1:
        raise ValueError(
            "Native cut cache geometry does not identify one authored profile"
        )
    return Matches[0]
