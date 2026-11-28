from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    RequireFields,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems, SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# active history boundaries and reciprocal allocation maps establish native operation ownership
def ReadSpanOps(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    History: JournalModel,
    BodyValue: BodyNode,
    BodyTag: FeatureTag,
) -> tuple[int, ...]:
    Stream = History.Stream
    if (
        Stream.CurrentStateId != Stream.MaxStateId
        or Stream.CurrentStateId != Context.Extrude.Fields["endModelHS"]
        or History.States[Stream.InitialNode].StateId
        != Context.Extrude.Fields["startModelHS"]
        or Stream.NextEntityTag <= BodyValue.Prefix.EntityTag
        or not BodyTag.PrimaryId.isdecimal()
    ):
        raise ValueError(
            "Native circular span history is rolled back or has inconsistent ownership"
        )
    Operation = int(BodyTag.PrimaryId)
    Manager = ResolveField(
        Graph, Context.Fragment, "rFeatureIdManager", "DcFeatureIdManager"
    )
    RequireFields(Manager, {"rOwnerFragment": LocalRef(Context.Fragment.ObjectId)})
    Forward = MappingItems(Manager.Fields["featureIdMap"])
    Reverse = MappingItems(Manager.Fields["enetityIdMap"])
    Indices = {
        IntegerValue(Entry.First): IntegerValue(Entry.Second) for Entry in Forward
    }
    Owners = {IntegerValue(Entry.First): SeriesItems(Entry.Second) for Entry in Reverse}
    Pairs = [
        (IntegerValue(KeyValue), Owner)
        for Owner, KeyList in Owners.items()
        for KeyValue in KeyList
    ]
    if (
        len(Indices) != len(Forward)
        or len(Owners) != len(Reverse)
        or set(Owners) != {Context.Extrude.ObjectId, Context.SketchFeature.ObjectId}
        or any(not KeyList for KeyList in Owners.values())
        or len(Pairs) != len(Indices)
        or dict(Pairs) != Indices
        or Indices.get(Operation) != Context.Extrude.ObjectId
    ):
        raise ValueError("Native circular span operation maps are not reciprocal")
    EmptyFields(Manager, ("obsoleteFeatureIds",))

    return tuple(IntegerValue(Value) for Value in Owners[Context.Extrude.ObjectId])
