from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import (
    CheckPrismProf,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.SavedScope.CheckSavedChain import (
    CheckSavedChain,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGraph import (
    CheckDimGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import (
    ReadLineDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import (
    ReadLineLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# reconstruction must use complete active typed contour and relation ownership instead of keyword profiles or guessed construction points
def ReadPrismLoop(
    ProfileValue: ArchiveNode, LinkValue: NativeLink, *, IsSaved: bool = False
) -> LineLoop:
    CheckPrismProf(ProfileValue, IsSaved=IsSaved)
    Fields = ProfileValue.FieldsValue
    if (
        Fields.get("f3dc") != 0
        or Fields.get("pd_f110") is not None
        or Fields.get("pd_has_fe8") != 0
    ):
        raise ValueError("cache free prism has shared or spatial profile ownership")
    SketchValue = RequireNative(Fields.get("pd_f80"), "sgSketch")
    if any(
        SketchValue.FieldsValue.get(FieldName) != 0
        for FieldName in ("f188", "f18c", "f190", "f578", "f134")
    ) or any(
        NativeRecord(SketchValue.FieldsValue.get("f570")).get(FieldName) != 0.0
        for FieldName in ("x", "y", "z")
    ):
        raise ValueError("cache free prism has unsupported sketch state")
    DimsValue = (
        None
        if IsLineState(SketchValue.FieldsValue.get("dims"))
        else ReadLineDims(SketchValue, LinkValue)
    )
    LoopValue = ReadLineLoop(SketchValue, LinkValue, DimsValue)
    if (
        len(LoopValue.PointsValue) != 4
        or len(LoopValue.LinesValue) != 4
        or LoopValue.RetiredRows
        or LoopValue.RetiredPointRows
        or LoopValue.RegionValues
    ):
        raise ValueError("cache free prism requires one fresh four line contour")
    if DimsValue is not None:
        CheckDimGraph(LoopValue, DimsValue)
    if IsSaved:
        CheckSavedChain(LinkValue, Fields.get("d5c0"), LoopValue)
    return LoopValue
