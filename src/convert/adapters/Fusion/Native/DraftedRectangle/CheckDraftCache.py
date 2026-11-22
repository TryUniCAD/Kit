from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    ObjectFields,
    SeriesItems,
    TextValue,
)
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# snapshot roots must resolve to current tool region and sketch identities before any retired sheet is accepted
def CheckDraftCache(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Snapshot: GeometryState,
) -> None:
    Count = Snapshot.Header.RootCount
    if (
        Count not in (4, 5)
        or len(Snapshot.Entities) != (168 if Count == 4 else 202)
        or Snapshot.Header
        != BrepHeader(23200, Count, 2, 10, 1e-6, 1e-10, Snapshot.Header.IntWidth)
        or Snapshot.Header.IntWidth not in (4, 8)
    ):
        raise ValueError("Unsupported native drafted snapshot profile")
    Roots = tuple(
        (Index, Value.TransformRef, Value.Prefix.Attribute, Value.Prefix.EntityTag)
        for Index, Value in enumerate(Snapshot.Entities)
        if isinstance(Value, BodyNode)
    )
    if Roots != tuple((Index, -1, -1, -1) for Index in range(1, Count)):
        raise ValueError(
            "Native drafted snapshot roots are not independent untransformed bodies"
        )
    Serializer = Graph.OneClass("BRepSerializer")
    if Model.Snapshots[0].Name != "Breps.BlobParts/" + TextValue(
        Serializer.Fields["partName"]
    ):
        raise ValueError("Native drafted snapshot is not the selected serializer part")
    Generator = ResolveField(
        Graph, Serializer, "topEntityPIDGenerator", "PassiveIdGenerator"
    )
    ScanOrder = tuple(
        IntegerValue(Value) for Value in SeriesItems(Generator.Fields["scanOrderIndex"])
    )
    Addresses = SeriesItems(Generator.Fields["addressOfTopEntities"])
    if (
        len(ScanOrder) != Count - 1
        or len(set(ScanOrder)) != len(ScanOrder)
        or min(ScanOrder) <= 0
        or IntegerValue(Generator.Fields["nextId"]) <= max(ScanOrder)
        or len(Addresses) != len(ScanOrder)
    ):
        raise ValueError(
            "Native drafted snapshot passive identities disagree with its roots"
        )
    ToolNode = ResolveField(
        Graph, Context.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody"
    )
    ToolCaches = LinkedNodes(Graph, ToolNode, "toolbodyCaches")
    RegionCaches = tuple(
        Value
        for Value in LinkedNodes(Graph, Graph.OneClass("SketchRegionRef"), "caches")
        if Value.ClassName == "ETCachedTopology"
    )
    if len(ToolCaches) != 1 or len(RegionCaches) != 1:
        raise ValueError(
            "Native drafted snapshot requires one tool and one region topology cache"
        )
    SameNodes((*ToolCaches, *RegionCaches), Graph.ByClass("ETCachedTopology"))
    for Index, Cache in enumerate((*ToolCaches, *RegionCaches)):
        Scope = ObjectFields(Cache.Fields["scope"])
        if (
            IntegerValue(Cache.Fields["cachedEntityId"]) != ScanOrder[Index]
            or Scope
            != {
                "assetId": Model.Asset.AssetId,
                "scopeEntityIdentifier": Context.Component.Fields["persistentId"],
                "scopeIdType": 2,
                "segmentId": 0,
            }
            or Cache.Fields["progenitor"] is not None
        ):
            raise ValueError(
                "Native drafted snapshot cache does not own its selected root"
            )
    if IntegerValue(Context.Sketch.Fields["bodyId"]) != ScanOrder[2]:
        raise ValueError(
            "Native drafted snapshot sketch root has a different passive identity"
        )
    if Count == 5 and ScanOrder[3] >= min(ScanOrder[:3]):
        raise ValueError(
            "Native drafted snapshot extra sheet is not a retired passive identity"
        )
