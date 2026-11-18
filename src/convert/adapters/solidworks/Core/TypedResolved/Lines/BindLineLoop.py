from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeProfile, NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGraph import (
    CheckDimGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineNativeDims import (
    LineNativeDims,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import (
    ReadLineDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import (
    ReadLineLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# only complete ordinary typed rings may supersede heuristic geometry while unsupported sketches remain intact
def BindLineLoop(
    Sketch: NativeSketch, NodeValue: ArchiveNode, LinkValue: NativeLink
) -> NativeSketch | None:
    if (
        NodeValue.FieldsValue.get("f3dc") != 0
        or NodeValue.FieldsValue.get("pd_f110") is not None
    ):
        return None
    try:
        SketchValue = RequireNative(NodeValue.FieldsValue.get("pd_f80"), "sgSketch")
        DimsValue = (
            None
            if IsLineState(SketchValue.FieldsValue.get("dims"))
            else ReadLineDims(SketchValue, LinkValue)
        )
        LoopValue = ReadLineLoop(SketchValue, LinkValue, DimsValue)
        if DimsValue is not None:
            CheckDimGraph(LoopValue, DimsValue)
    except (ValueError, TypeError, KeyError):
        return None
    return ReplaceValue(
        Sketch,
        TypedLines=LoopValue,
        profiles=(
            NativeProfile(
                "line-loop",
                tuple(
                    Coordinate
                    for Point in LoopValue.PointsValue
                    for Coordinate in Point.PositionValue
                ),
                (),
            ),
        ),
        dimensions=LineNativeDims(DimsValue),
        constraints=(),
    )
