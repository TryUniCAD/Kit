from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGraph import (
    CheckDimGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import (
    ReadLineDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineScope import (
    CheckLineScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineOrder import LineOrder
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLinePoint import (
    ReadLinePoint,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineSegment import (
    ReadLineSegment,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# qualified local equations need the actual constrained contour and the extra noncontour origin proxy
def ReadEqLoop(ProfileValue: ArchiveNode, LinkValue: NativeLink) -> LineLoop:
    if (
        ProfileValue.FieldsValue.get("f3dc") != 0
        or ProfileValue.FieldsValue.get("pd_f110") is not None
    ):
        raise ValueError("local equation requires an ordinary unsuppressed profile")
    SketchValue = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    Fields = SketchValue.FieldsValue
    CheckLineScope(Fields, PartRelations=True)
    DimsValue = ReadLineDims(SketchValue, LinkValue)
    OriginValue = DimsValue.OriginValue
    Points = NativeRows(Fields.get("points"))
    Lines = NativeRows(Fields.get("lines"))
    if (
        OriginValue is None
        or OriginValue.ExternalIndex != 4
        or OriginValue.LocalIndex != 0
        or len(Points) != 5
        or len(Lines) != 4
        or Fields.get("npoints") != len(Points)
        or Fields.get("nlines") != len(Lines)
    ):
        raise ValueError(
            "local equation needs the four point contour and its actual origin proxy"
        )
    Vertices = tuple(
        ReadLinePoint(
            RowValue, Index, DimsValue.ReferencesValue.get(("point", Index), 0)
        )
        for Index, RowValue in enumerate(Points[:4])
    )
    Segments = tuple(
        ReadLineSegment(
            RowValue, Index, DimsValue.ReferencesValue.get(("line", Index), 0)
        )
        for Index, RowValue in enumerate(Lines)
    )
    LoopValue = LineLoop(
        Vertices,
        Segments,
        LineOrder(Vertices, Segments),
        NativeNodeSpan(LinkValue, SketchValue),
        DimsValue,
    )
    CheckDimGraph(LoopValue, DimsValue)
    return LoopValue
