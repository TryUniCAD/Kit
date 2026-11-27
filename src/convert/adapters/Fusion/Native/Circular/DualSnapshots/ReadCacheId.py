from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, TextValue
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# cached body identities must resolve through the actual owning component scope rather than numeric coincidence
def ReadCacheId(
    Graph: NativeGraph,
    Owner: NativeNode,
    FieldName: str,
    AssetId: str,
    Component: NativeNode,
) -> int:
    Values = LinkedNodes(Graph, Owner, FieldName)
    if len(Values) != 1 or Values[0].ClassName != "ETCachedTopology":
        raise ValueError("Dual snapshot requires one owned cached topology reference")
    CacheValue = Values[0]
    if (
        ObjectFields(CacheValue.Fields["scope"])
        != {
            "assetId": AssetId,
            "scopeEntityIdentifier": TextValue(Component.Fields["persistentId"]),
            "scopeIdType": 2,
            "segmentId": Component.SegmentId,
        }
        or CacheValue.Fields["progenitor"] is not None
    ):
        raise ValueError("Dual snapshot cached topology identifies another scope")
    return IntegerValue(CacheValue.Fields["cachedEntityId"])
