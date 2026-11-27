from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimCircle import (
    CheckRimCircle,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    CheckIdentity,
    ObjectFields,
    TextValue,
)
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph


# exact cache ownership keeps the extra selected edge caches from being omitted or aliased
def CheckRimCaches(Graph: NativeGraph, Context: RimContext, AssetId: str) -> None:
    Extrusion = Context.Extrusion
    Selected = ResolveField(Graph, Context.EdgeData, "connectedEdgeRef", "ModelDataRef")
    Circles = LinkedNodes(Graph, Context.SelectedRef, "caches")
    SameNodes(Circles, Graph.ByClass("ETCachedCircleArc"))
    if len(Circles) != 1:
        raise ValueError("Native rim selected reference requires one cached circle")
    CheckRimCircle(Graph, Context, Circles[0])
    Matrix = ResolveField(
        Graph, Extrusion.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    (Profile,) = LinkedNodes(Graph, Extrusion.Extrude, "profileDataRefs")
    if any(
        len(LinkedNodes(Graph, Owner, "caches")) != 1
        for Owner in (Matrix, Profile, Selected)
    ):
        raise ValueError(
            "Native rim matrix caches require one distinct source owner each"
        )
    SameNodes(
        (
            *LinkedNodes(Graph, Matrix, "caches"),
            *LinkedNodes(Graph, Profile, "caches"),
            *LinkedNodes(Graph, Selected, "caches"),
        ),
        Graph.ByClass("ETCachedMatrix3d"),
    )
    (Datum,) = LinkedNodes(Graph, Matrix, "dataRefs")
    if len(LinkedNodes(Graph, Datum, "caches")) != 1:
        raise ValueError("Native rim datum requires one cached plane")
    SameNodes(LinkedNodes(Graph, Datum, "caches"), Graph.ByClass("ETCachedPlane"))
    (Region,) = LinkedNodes(Graph, Profile, "dataRefs")
    ToolBody = ResolveField(
        Graph, Extrusion.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody"
    )
    SameNodes(
        (
            *LinkedNodes(Graph, Region, "caches"),
            *LinkedNodes(Graph, ToolBody, "toolbodyCaches"),
        ),
        Graph.ByClass("ETCachedTopology"),
    )
    for Value in Graph.ByClass("ETCachedMatrix3d"):
        CheckIdentity(Value.Fields["rCachedGeometry"])
        CheckIdentity(Value.Fields["sketchTransf"])
        RequireFields(Value, {"progenitor": None})
    for Value in Graph.ByClass("ETCachedTopology"):
        RequireFields(Value, {"progenitor": None})
        if (
            ObjectFields(Value.Fields["scope"])
            != {
                "assetId": AssetId,
                "scopeEntityIdentifier": TextValue(
                    Extrusion.Component.Fields["persistentId"]
                ),
                "scopeIdType": 2,
                "segmentId": 0,
            }
            or IntegerValue(Value.Fields["cachedEntityId"]) <= 0
        ):
            raise ValueError(
                "Native rim cached topology has inconsistent scope or identity"
            )
