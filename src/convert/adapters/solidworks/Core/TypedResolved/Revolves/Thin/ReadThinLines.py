from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
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


from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.CheckThinRels import (
    CheckThinRels,
)

from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ReadThinEdge import (
    ReadThinEdge,
)


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
