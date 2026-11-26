from convert.adapters.Fusion.Native.Cuts.CheckCutFace import CheckCutFace
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBodyFaces import ReadBodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Planar.CheckEdgeUses import CheckEdgeUses
from convert.Formats.Fusion.BrepCodec.Journal.Planar.CheckLineEdge import CheckLineEdge
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# matching every closed native face proves the nonconvex solid without weakening the convex reader
def CheckCutSolid(
    Table: LiveTable, BodyRef: int, Rings: tuple[tuple[KJournalVector, ...], ...]
) -> None:
    Faces = ReadBodyFaces(Table, BodyRef)
    CheckEdgeUses(Table, Faces)
    Matches = tuple(CheckCutFace(Table, FaceValue, Rings) for FaceValue in Faces)
    if len(Matches) != len(Rings) or set(Matches) != set(range(len(Rings))):
        raise ValueError(
            "Native cut solid has missing or duplicate physical boundaries"
        )
    for EdgeRef in {
        Value.EdgeRef for FaceValue in Faces for Value in FaceValue.BoundaryUses
    }:
        CheckLineEdge(Table, EdgeRef)
