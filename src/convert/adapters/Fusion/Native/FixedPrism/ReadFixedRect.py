from convert.adapters.Fusion.Native.FixedPrism.ReadFixAnchor import ReadFixAnchor
from convert.adapters.Fusion.Native.FixedPrism.ReadFixedDims import ReadFixedDims
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, SameNodes
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.OrderLines import OrderLines
from convert.adapters.Fusion.Native.Rectangle.ReadRectAxes import ReadRectAxes
from convert.adapters.Fusion.Native.Rectangle.ReadRectUnits import ReadRectUnits
from convert.adapters.Fusion.Native.Rectangle.RectSketchProof import RectSketchProof
from interchange.Enums.EnumUnits import UnitSystem


# the fixed corner is a point property and must never manufacture a geometric coincidence
def ReadFixedRect(Graph: NativeGraph, Context: ExtrudeContext) -> RectSketchProof:
    DisplayUnit = ReadRectUnits(Graph)
    if DisplayUnit is not UnitSystem.KMillimeter:
        raise ValueError("Native fixed rectangle requires millimeter display units")
    Rules = LinkedNodes(Graph, Context.Sketch, "constraints")
    Dimensions = LinkedNodes(Graph, Context.Sketch, "dimensions")
    SameNodes(Rules, Graph.ByClass("SketchGeomConstraint"))
    SameNodes(Dimensions, Graph.ByClass("FusionSketchLinearDim"))
    Lines = OrderLines(Graph, Graph.ByClass("Line3D"))
    Anchor, Origin = ReadFixAnchor(Graph, Lines)
    AxisRules = ReadRectAxes(Graph, Context, Rules, None, Lines)
    Bindings, Params, SizeRules = ReadFixedDims(
        Graph, Context, Dimensions, Lines, Anchor
    )
    Normals = {PointCoords(LineValue.Fields["planeNormal"]) for LineValue in Lines}
    if Normals not in ({(0.0, 0.0, -1.0)}, {(0.0, 0.0, 1.0)}):
        raise ValueError("Native fixed rectangle requires a uniform XY line normal")
    Normal = Normals.pop()
    return RectSketchProof(
        Rules,
        Dimensions,
        Bindings,
        Params,
        Anchor,
        Origin,
        (*AxisRules, *SizeRules),
        DisplayUnit,
        Normal,
    )
