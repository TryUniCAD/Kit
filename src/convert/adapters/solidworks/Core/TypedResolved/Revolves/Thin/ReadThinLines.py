from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGroups import (
    CheckDimGroups,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import (
    ReadDimRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineEntity import (
    CheckLineEntity,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineScope import (
    CheckLineScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineIndex import LineIndex
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Revolves.AxisReference import (
    AxisReference,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadAxisLine import (
    ReadAxisLine,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.ReadAxisPoint import (
    ReadAxisPoint,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.RevolveProfile import (
    RevolveProfile,
)


# thin body incidence uses its native open line flag and two live endpoints
def ReadThinEdge(RowValue: Mapping[str, object]) -> LineSegment:
    FieldsValue = NativeRecord(RowValue.get("line"))
    CheckLineEntity(FieldsValue, FlagsValue=68)
    Permanent = FieldsValue.get("f08")
    Creation = FieldsValue.get("f0c")
    if (
        RowValue.get("flags") != 0
        or FieldsValue.get("fd0") != 1
        or FieldsValue.get("fd4") != 0
        or FieldsValue.get("fe8") != 0
        or type(Permanent) is not int
        or Permanent <= 0
        or type(Creation) is not int
        or Creation <= 0
    ):
        raise ValueError("SOLIDWORKS thin sketch requires its actual open body line")
    return LineSegment(
        0,
        Permanent,
        Creation,
        LineIndex(FieldsValue, "fc8_s", "fc8", 65535),
        LineIndex(FieldsValue, "fcc_s", "fcc", 65535),
        FieldsValue,
    )


# the measured open profile has no solver rows or hidden region owners
def CheckThinRels(FieldsValue: Mapping[str, object]) -> None:
    CheckLineScope(FieldsValue, HasDrivers=True)
    GroupsValue = NativeRecord(FieldsValue.get("dims"))
    CheckDimGroups(GroupsValue)
    if (
        ReadDimRows(GroupsValue, "ng2", "val_g2")
        or ReadDimRows(GroupsValue, "nlog1", "log_g1")
        or not IsLineState(GroupsValue.get("f118"))
    ):
        raise ValueError("SOLIDWORKS thin sketch has unqualified solver relations")


# exactly two native lines with disjoint point owners are required before projecting the open sketch
def ReadThinLines(
    LinkValue: NativeLink, SketchValue: ArchiveNode, Reference: AxisReference
) -> RevolveProfile:
    FieldsValue = SketchValue.FieldsValue
    CheckThinRels(FieldsValue)
    PointsValue = NativeRows(FieldsValue.get("points"))
    LinesValue = NativeRows(FieldsValue.get("lines"))
    if (
        len(LinesValue) != 2
        or FieldsValue.get("nlines") != 2
        or len(PointsValue) != 4
        or FieldsValue.get("npoints") != 4
        or Reference.IndexValue != 1
    ):
        raise ValueError(
            "SOLIDWORKS thin sketch requires two actual lines and four points"
        )
    BodyValue = ReadThinEdge(LinesValue[0])
    AxisValue = ReadAxisLine(LinesValue[1], Reference)
    if (
        (
            BodyValue.StartValue,
            BodyValue.EndValue,
            AxisValue.StartValue,
            AxisValue.EndValue,
        )
        != (0, 1, 2, 3)
        or BodyValue.PermanentId == AxisValue.PermanentId
        or BodyValue.CreationId == AxisValue.CreationId
    ):
        raise ValueError("SOLIDWORKS thin sketch axis and body incidence overlap")
    BodyPoints = tuple(ReadAxisPoint(PointsValue[Index], Index, 0) for Index in (0, 1))
    AxisPoints = {
        Index: ReadAxisPoint(PointsValue[Index], Index, 1) for Index in (2, 3)
    }
    LoopValue = LineLoop(
        BodyPoints, (BodyValue,), (0,), NativeNodeSpan(LinkValue, SketchValue)
    )
    return RevolveProfile(LoopValue, AxisValue, AxisPoints, (), ())
