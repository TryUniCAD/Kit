from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Graph.SketchContexts import KSketchContexts
from convert.adapters.Fusion.Native.Policy.CheckMeshAbsent import CheckMeshAbsent

# the empty classes order must stay explicit so public document claims remain grounded in native records
KEmptyClasses = (
    "AssyConstraints",
    "AssyConstraintOccurrences",
    "ContactSets",
    "JointOrigins",
    "MotionStudies",
    "SurfaceGroups",
    "SelectionGroups",
    "WorkGeometryCustomGroups",
    "SketchCustomGroups",
    "SubDSurfaceNodes",
    "Canvases",
    "DcGroupFeatures",
    "DecalPatches",
    "PMIAnnotations",
    "MeshBodies",
    "CanvasGroups",
    "LatticeRigDeformers",
    "VisualAnalyses",
    "NamedTrackedEntitySet",
    "WorkingModelPlaceholderRoot",
    "Arrangements",
    "ComponentInstances",
)


# invalid containers input must fail here so public document claims remain grounded in native records
def CheckContainers(
    Graph: NativeGraph,
    Context: KSketchContexts,
    SketchNodes: tuple[NativeNode, ...] | None = None,
) -> None:
    for ClassName in KEmptyClasses:
        for NodeValue in Graph.ByClass(ClassName):
            if "children" in NodeValue.Fields:
                EmptyFields(NodeValue, ("children",))
    CheckMeshAbsent(Graph, Context.Component)
    Sketches = ResolveField(Graph, Context.Component, "rSketches", "Sketches")
    Expected = SketchNodes if SketchNodes is not None else (Context.Sketch,)
    SameNodes(Expected, LinkedNodes(Graph, Sketches, "children"))
    SameNodes(Expected, Graph.ByClass("MSketch"))
    Features = ResolveField(Graph, Context.Component, "m_rFeatures", "Features")
    EmptyFields(Features, ("children",))
    if Features.Fields["m_curFeatureId"] != 1:
        raise ValueError("Unsupported native legacy Features state")
    CacheBodies = ResolveField(Graph, Context.Component, "rCacheBodies", "Bodies")
    EmptyFields(CacheBodies, ("children", "groupChildren"))
    for NodeValue in (
        Graph.ByClass("WorkPlane")
        + Graph.ByClass("WorkAxis")
        + Graph.ByClass("WorkPoint")
    ):
        if (
            NodeValue.Fields["isOrigin"] is not True
            or NodeValue.Fields["rDcNode"] is not None
        ):
            raise ValueError("Unmodeled native construction feature")
