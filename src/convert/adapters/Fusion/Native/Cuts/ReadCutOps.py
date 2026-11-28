from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    ResolveField,
    RequireFields,
    EmptyFields,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems, SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# reciprocal operation allocation must account for every timeline feature and no external owner
def ReadCutOps(
    Graph: NativeGraph, Contexts: tuple[ExtrudeContext, ExtrudeContext]
) -> dict[int, tuple[int, ...]]:
    Fragment = Contexts[0].Fragment
    Manager = ResolveField(Graph, Fragment, "rFeatureIdManager", "DcFeatureIdManager")
    RequireFields(Manager, {"rOwnerFragment": LocalRef(Fragment.ObjectId)})
    Forward = MappingItems(Manager.Fields["featureIdMap"])
    Reverse = MappingItems(Manager.Fields["enetityIdMap"])
    Indices = {
        IntegerValue(Entry.First): IntegerValue(Entry.Second) for Entry in Forward
    }
    Owners = {
        IntegerValue(Entry.First): tuple(
            IntegerValue(ItemValue) for ItemValue in SeriesItems(Entry.Second)
        )
        for Entry in Reverse
    }
    Pairs = [
        (Operation, Owner)
        for Owner, Operations in Owners.items()
        for Operation in Operations
    ]
    Expected = {
        Value.ObjectId
        for Context in Contexts
        for Value in (Context.SketchFeature, Context.Extrude)
    }
    if (
        len(Indices) != len(Forward)
        or len(Owners) != len(Reverse)
        or set(Owners) != Expected
        or any(not Operations for Operations in Owners.values())
        or len(Pairs) != len(Indices)
        or dict(Pairs) != Indices
    ):
        raise ValueError("Native cut operation ownership is incomplete or inconsistent")
    EmptyFields(Manager, ("obsoleteFeatureIds",))
    return Owners
