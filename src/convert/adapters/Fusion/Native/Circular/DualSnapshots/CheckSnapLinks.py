from convert.adapters.Fusion.Native.Circular.DualSnapshots.ReadCacheId import (
    ReadCacheId,
)
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    SeriesItems,
    TextValue,
)
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# passive body scan order must bind snapshot solid profile and sketch roles to selected native owners
def CheckSnapLinks(
    Model: DocumentModel,
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Roles: tuple[str, ...],
) -> None:
    CacheBodies = ResolveField(Graph, Context.Component, "rCacheBodies", "Bodies")
    RequireFields(
        CacheBodies,
        {"rParent": LocalRef(Context.Component.ObjectId), "alterateBodies": False},
    )
    SameNodes((), LinkedNodes(Graph, CacheBodies, "children"))
    SameNodes((), LinkedNodes(Graph, CacheBodies, "groupChildren"))
    Serializer = ResolveField(Graph, CacheBodies, "rBRepSerializer", "BRepSerializer")
    SameNodes((Serializer,), Graph.ByClass("BRepSerializer"))
    RequireFields(
        Serializer, {"rBodies": LocalRef(CacheBodies.ObjectId), "rBody": None}
    )
    if Model.Snapshots[0].Name != "Breps.BlobParts/" + TextValue(
        Serializer.Fields["partName"]
    ) or MappingItems(Serializer.Fields["mapBodyId"]):
        raise ValueError("Dual snapshot serializer name or body map disagrees")
    Generator = ResolveField(
        Graph, Serializer, "topEntityPIDGenerator", "PassiveIdGenerator"
    )
    RequireFields(Generator, {"rBodies": None, "rBody": None})
    ToolValue = ResolveField(
        Graph, Context.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody"
    )
    if Graph.Resolve(ToolValue.Fields["rExtrudeFeature"]) != Context.Extrude:
        raise ValueError("Dual snapshot tool does not belong to its extrusion")
    (Profile,) = LinkedNodes(Graph, Context.Extrude, "profileDataRefs")
    (Region,) = LinkedNodes(Graph, Profile, "dataRefs")
    if Profile.ClassName != "ModelDataRef" or Region.ClassName != "SketchRegionRef":
        raise ValueError("Dual snapshot profile cache has an incompatible source owner")
    SameNodes(
        (
            *LinkedNodes(Graph, ToolValue, "toolbodyCaches"),
            *LinkedNodes(Graph, Region, "caches"),
        ),
        Graph.ByClass("ETCachedTopology"),
    )
    RoleIds = {
        "solid": ReadCacheId(
            Graph, ToolValue, "toolbodyCaches", Model.Asset.AssetId, Context.Component
        ),
        "profile": ReadCacheId(
            Graph, Region, "caches", Model.Asset.AssetId, Context.Component
        ),
        "sketch": IntegerValue(Context.Sketch.Fields["bodyId"]),
    }
    Expected = tuple(RoleIds[RoleName] for RoleName in Roles)
    Actual = tuple(
        IntegerValue(Value) for Value in SeriesItems(Generator.Fields["scanOrderIndex"])
    )
    Addresses = tuple(
        IntegerValue(Value)
        for Value in SeriesItems(Generator.Fields["addressOfTopEntities"])
    )
    if (
        len(set(Expected)) != 3
        or min(Expected) <= 0
        or Actual != Expected
        or len(Addresses) != 3
        or len(set(Addresses)) != 3
        or min(Addresses) <= 0
        or IntegerValue(Generator.Fields["nextId"]) <= max(Expected)
    ):
        raise ValueError(
            "Dual snapshot body roles disagree with native passive identities"
        )
