from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField, SameNodes
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Rectangle.ReadRectDim import ReadRectDim
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.geometry.Models.Sketch import SketchRelation


# fixed rectangle dimensions carry their own axis and must each resolve one real sketch binding
def BindFixAxes(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Dimensions: tuple[NativeNode, ...],
    BindingParams: tuple[tuple[NativeNode, NativeNode], ...],
    Lines: tuple[NativeNode, ...],
    Anchor: NativeNode,
) -> tuple[SketchRelation, ...]:
    Kinds = {1 << 22: ConstraintKind.KDistanceX, 1 << 23: ConstraintKind.KDistanceY}
    Codes = tuple(IntegerValue(Value.Fields["constraintType"]) for Value in Dimensions)
    if set(Codes) != Kinds.keys():
        raise ValueError("Native fixed rectangle requires one dimension on each axis")
    Bindings = tuple(
        ResolveField(Graph, Dimension, "dcParameter", "DcDoubleParameter")
        for Dimension in Dimensions
    )
    SameNodes(Bindings, tuple(Binding for Binding, _ in BindingParams))
    Params = {Binding.Identity: Param for Binding, Param in BindingParams}
    return tuple(
        ReadRectDim(
            Graph,
            Context,
            Dimension,
            Binding,
            Params[Binding.Identity],
            Lines,
            Anchor,
            Kinds[CodeValue],
            Fixed=True,
        )
        for Dimension, Binding, CodeValue in zip(
            Dimensions, Bindings, Codes, strict=True
        )
    )
