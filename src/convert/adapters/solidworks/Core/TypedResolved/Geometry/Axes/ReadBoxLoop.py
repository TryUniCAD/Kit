from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import (
    CheckPrismProf,
)
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
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the named box requires an independently driven local rectangle coincident with the actual origin
def ReadBoxLoop(ProfileValue: ArchiveNode, LinkValue: NativeLink) -> LineLoop:
    CheckPrismProf(ProfileValue)
    SketchValue = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    Fields = SketchValue.FieldsValue
    CheckLineScope(Fields, HasDims=True)
    if any(
        Fields.get(NameValue) != 0
        for NameValue in ("f188", "f18c", "f190", "f578", "f134")
    ) or any(
        NativeRecord(Fields.get("f570")).get(NameValue) != 0.0
        for NameValue in ("x", "y", "z")
    ):
        raise ValueError("cache free box has unsupported sketch state")
    DimsValue = ReadLineDims(SketchValue, LinkValue)
    OriginValue = DimsValue.OriginValue
    Points = NativeRows(Fields.get("points"))
    Lines = NativeRows(Fields.get("lines"))
    if (
        (len(Points), len(Lines), Fields.get("npoints"), Fields.get("nlines"))
        != (5, 4, 5, 4)
        or OriginValue is None
        or OriginValue.ExternalIndex != 4
    ):
        raise ValueError("cache free box has no complete origin attached rectangle")
    References = DimsValue.ReferencesValue
    PointsValue = tuple(
        ReadLinePoint(RowValue, Index, References.get(("point", Index), 0))
        for Index, RowValue in enumerate(Points[:4])
    )
    LinesValue = tuple(
        ReadLineSegment(RowValue, Index, References.get(("line", Index), 0))
        for Index, RowValue in enumerate(Lines)
    )
    LoopValue = LineLoop(
        PointsValue,
        LinesValue,
        LineOrder(PointsValue, LinesValue),
        NativeNodeSpan(LinkValue, SketchValue),
        DimsValue,
    )
    CheckDimGraph(LoopValue, DimsValue)
    return LoopValue
