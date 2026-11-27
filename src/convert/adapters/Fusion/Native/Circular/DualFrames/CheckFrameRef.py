from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# a coincident matrix cannot substitute for the actual owned origin plane recipe
def CheckFrameRef(
    Graph: NativeGraph, Context: ExtrudeContext
) -> tuple[NativeNode, NativeNode, NativeNode]:
    Matrix = ResolveField(
        Graph, Context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    References = LinkedNodes(Graph, Matrix, "dataRefs")
    if len(References) != 1:
        raise ValueError("Native dual frame requires one selected plane reference")
    Reference = References[0]
    Recipe = ResolveField(Graph, Reference, "rRecipe", "EntityRecipe")
    Datum = Graph.ResolveId(Recipe.Fields["m_entityId"])
    Origin = ResolveField(
        Graph, Context.Component, "m_rOriginWorkGeometry", "OriginWorkGeometry"
    )
    if (
        Datum.ClassName != "WorkPlane"
        or Datum not in LinkedNodes(Graph, Origin, "children")
        or Graph.Resolve(Datum.Fields["rParent"]) != Origin
        or Graph.Resolve(Origin.Fields["rParent"]) != Context.Component
    ):
        raise ValueError("Native dual frame does not select the owned origin datum")
    if Datum.Fields["originName"] not in ("XY", "XZ"):
        raise ValueError("Native dual frame requires a qualified principal datum")
    RequireFields(Datum, {"isOrigin": True, "rDcNode": None})
    if (
        Graph.Resolve(Context.Plane.Fields["rParent"]) != Context.Component
        or Graph.Resolve(Context.Sketch.Fields["UCS"]) != Context.Plane
    ):
        raise ValueError("Native dual frame coordinate system has another owner")
    if (
        Graph.Resolve(Context.Sketch.Fields["rDcNode"]) != Context.SketchFeature
        or Graph.Resolve(Context.SketchFeature.Fields["rSketch"]) != Context.Sketch
    ):
        raise ValueError("Native dual frame sketch ownership is not reciprocal")
    return Matrix, Reference, Datum
