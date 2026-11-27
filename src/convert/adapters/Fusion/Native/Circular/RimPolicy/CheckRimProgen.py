from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import RequireFields, ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair


# feature progenitor allocation must preserve each actual owner without duplicate tag aliases
def CheckRimProgen(Graph: NativeGraph, Context: RimContext) -> None:
    for Feature in (
        Context.Extrusion.SketchFeature,
        Context.Extrusion.Extrude,
        Context.Feature,
    ):
        Table = ResolveField(Graph, Feature, "rProgenitorTable", "ProgenitorTable")
        Entries = SeriesItems(Table.Fields["ProgenitorTagVec"])
        if any(not isinstance(Entry, ValuePair) for Entry in Entries):
            raise ValueError("Native rim progenitor allocation requires typed pairs")
        TagGroups = tuple(
            IntegerValue(Entry.Second)
            for Entry in Entries
            if isinstance(Entry, ValuePair)
        )
        if (
            len(set(TagGroups)) != len(TagGroups)
            or (TagGroups and min(TagGroups) <= 0)
            or IntegerValue(Table.Fields["tagId"]) <= max(TagGroups, default=0)
        ):
            raise ValueError("Native rim progenitor tags disagree with their allocator")
        if len(
            {
                Graph.Resolve(Entry.First).Identity
                for Entry in Entries
                if isinstance(Entry, ValuePair)
            }
        ) != len(Entries):
            raise ValueError("Native rim progenitor allocation repeats a source owner")
        RequireFields(Table, {"rParent": None})
