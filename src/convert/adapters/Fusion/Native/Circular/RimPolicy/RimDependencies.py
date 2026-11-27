from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph


# role derived dependency arcs preserve the actual construction order without captured entity identifiers
def RimDependencies(
    Graph: NativeGraph, Context: RimContext
) -> set[tuple[str, str, int]]:
    Extrusion = Context.Extrusion
    Component = Graph.OneClass("DcComponent")
    Matrix = ResolveField(
        Graph, Extrusion.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    (Datum,) = LinkedNodes(Graph, Matrix, "dataRefs")
    (Profile,) = LinkedNodes(Graph, Extrusion.Extrude, "profileDataRefs")
    (Region,) = LinkedNodes(Graph, Profile, "dataRefs")
    ToolBody = ResolveField(
        Graph, Extrusion.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody"
    )
    Selected = ResolveField(Graph, Context.EdgeData, "connectedEdgeRef", "ModelDataRef")
    Edges = (
        (Component, Extrusion.SketchFeature, 4096),
        (Matrix, Extrusion.SketchFeature, 1),
        (Datum, Matrix, 1),
        (Component, Extrusion.Extrude, 4096),
        (ToolBody, Extrusion.Extrude, 1),
        (Region, Profile, 1),
        (Extrusion.SketchFeature, Region, 4),
        (Profile, ToolBody, 1),
        (Extrusion.Along, ToolBody, 1),
        (Extrusion.Taper, ToolBody, 1),
        (Component, Context.Feature, 4096),
        (Extrusion.Extrude, Context.Feature, 1024),
        (Selected, Context.Feature, 1),
        (Context.Weight, Context.Feature, 1),
        (Context.Radius, Context.Feature, 1),
        (Context.SelectedRef, Selected, 1),
        (Extrusion.Extrude, Context.SelectedRef, 1),
    )
    return {(First.Identity, Second.Identity, Flags) for First, Second, Flags in Edges}
