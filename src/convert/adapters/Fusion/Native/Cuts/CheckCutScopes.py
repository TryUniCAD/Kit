from convert.adapters.Fusion.Native.Graph.GraphValues import (
    ObjectFields,
    TextValue,
    CheckIdentity,
)
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    SameNodes,
    ResolveField,
    LinkedNodes,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext


# every passive scope must name one of the actual owned sketches or the common component
def CheckCutScopes(
    Graph: NativeGraph, Contexts: tuple[ExtrudeContext, ExtrudeContext], AssetId: str
) -> None:
    SketchIds = {str(Context.Sketch.ObjectId) for Context in Contexts}
    ComponentId = TextValue(Contexts[0].Component.Fields["persistentId"])
    for NodeValue in Graph.Nodes.values():
        if NodeValue.SegmentId != 0 or "rScope" not in NodeValue.Fields:
            continue
        Scope = ObjectFields(NodeValue.Fields["rScope"])
        Expected: set[str] = (
            SketchIds
            if Scope["scopeIdType"] == 1
            else {ComponentId} if Scope["scopeIdType"] == 2 else set()
        )
        if (
            Scope["assetId"] != AssetId
            or Scope["segmentId"] != 0
            or Scope["scopeEntityIdentifier"] not in Expected
        ):
            raise ValueError("Native cut passive scope escapes its owned history")
    Instance = Graph.OneClass("ComponentInstance")
    if "initialTransform" in Instance.Fields:
        CheckIdentity(Instance.Fields["initialTransform"])
    Nodes = ResolveField(Graph, Contexts[0].Fragment, "rNodes", "DcNodes")
    SameNodes(
        tuple(
            Value
            for Value in Graph.Nodes.values()
            if Value.SegmentId == 0 and Graph.HasBase(Value, "DcNode")
        ),
        LinkedNodes(Graph, Nodes, "children"),
    )
