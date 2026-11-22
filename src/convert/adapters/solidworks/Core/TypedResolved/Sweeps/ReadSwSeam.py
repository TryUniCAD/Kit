from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwArc import SwArcPoints
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwDriver import (
    CheckSwIndex,
)
from interchange.geometry.Models.VectorPlane import PlaneVector


# a saved full circle owns one point shared by the start and end incidences
@DataClass(frozen=True, slots=True)
class SwSeamPoint:
    PointValue: PlaneVector
    CenterIndex: int
    SeamIndex: int
    MarkValues: tuple[int, int]


# source incidence survives an edit even when the saved kernel chooses a different parameter seam
def ReadSwSeam(SketchValue: ArchiveNode) -> SwSeamPoint:
    FirstRow, SeamRow = NativeRows(SketchValue.FieldsValue.get("points"))
    FirstPoint, SeamPoint = (
        NativeRecord(Value.get("point")) for Value in (FirstRow, SeamRow)
    )
    FirstMark, SeamMark = FirstPoint.get("f0c"), SeamPoint.get("f0c")
    if (
        type(FirstMark) is not int
        or type(SeamMark) is not int
        or min(FirstMark, SeamMark) <= 0
        or FirstMark == SeamMark
        or FirstPoint.get("h1") is not None
        or FirstPoint.get("h2") is not None
        or SeamPoint.get("h2") is not None
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep section has ambiguous persistent point ownership"
        )
    _, SeamValue = SwArcPoints(SketchValue)
    CheckSwIndex(SeamPoint.get("h1"), "sgArcHandle", 0)
    return SwSeamPoint(SeamValue, 0, 1, (FirstMark, SeamMark))
