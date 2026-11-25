from convert.adapters.Fusion.Native.FixedPrism.CheckFixBind import CheckFixBind
from convert.adapters.Fusion.Native.FixedPrism.CheckFixTable import CheckFixTable
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Rectangle.ReadRectDims import (
    CheckRectDeps,
    ReadRectDim,
)
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.geometry.Models.Sketch import SketchRelation


# fixed rectangle dimension ownership must survive allocation changes after a native save
def ReadFixedDims(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Dimensions: tuple[NativeNode, ...],
    Lines: tuple[NativeNode, ...],
    Anchor: NativeNode,
) -> tuple[tuple[NativeNode, ...], tuple[NativeNode, ...], tuple[SketchRelation, ...]]:
    SketchBindings = LinkedNodes(Graph, Context.SketchFeature, "dcParameters")
    if len(SketchBindings) != 2 or len(Dimensions) != 2:
        raise ValueError(
            "Native fixed rectangle requires two sketch dimension bindings"
        )
    Bindings = (*SketchBindings, Context.Along, Context.Taper)
    SameNodes(Bindings, Graph.ByClass("DcDoubleParameter"))
    Owners = (Context.SketchFeature,) * 2 + (Context.Extrude,) * 2
    Table = ResolveField(Graph, Context.Component, "rParameterTable", "ParameterTable")
    DcNodes = ResolveField(Graph, Context.Fragment, "rNodes", "DcNodes")
    Children = LinkedNodes(Graph, DcNodes, "children")
    Slots = {IntegerValue(Binding.Fields["rparamId"]) for Binding in Bindings}
    RequireFields(Context.Fragment, {"nextParamId": len(Bindings)})
    if Slots != set(range(1, len(Bindings) + 1)) or any(
        Children.count(Binding) != 1 for Binding in Bindings
    ):
        raise ValueError("Native fixed rectangle binding allocation is inconsistent")
    Params = tuple(
        CheckFixBind(Graph, Binding, Owner, Table, DcNodes, Index == 3)
        for Index, (Binding, Owner) in enumerate(zip(Bindings, Owners, strict=True))
    )
    CheckFixTable(Graph, Table, Params)
    CheckRectDeps(Graph, Context, SketchBindings)
    Relations = tuple(
        ReadRectDim(
            Graph,
            Context,
            Dimension,
            Binding,
            Param,
            Lines,
            Anchor,
            KindValue,
            Fixed=True,
        )
        for Dimension, Binding, Param, KindValue in zip(
            Dimensions,
            SketchBindings,
            Params[:2],
            (ConstraintKind.KDistanceX, ConstraintKind.KDistanceY),
            strict=True,
        )
    )
    Ranks = tuple(
        Dimension.Frame.Subjects[0].ObserverIndex
        for Dimension in Dimensions
        if Dimension.Frame.Subjects
    )
    if Ranks not in ((0, 1), (4, 5)):
        raise ValueError(
            "Native fixed rectangle dimension settings observer ranks disagree"
        )
    return SketchBindings, Params[:2], Relations
