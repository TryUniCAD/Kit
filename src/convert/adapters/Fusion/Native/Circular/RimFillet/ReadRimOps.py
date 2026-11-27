from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Circular.Spans.ReadSpanProgen import ReadSpanProgen
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag


# active body and fillet operations must resolve through their real allocation and progenitor owners
def ReadRimOps(
    Graph: NativeGraph, Context: RimContext, BodyTag: FeatureTag
) -> tuple[int, int]:
    Extrusion = Context.Extrusion
    Manager = ResolveField(
        Graph, Extrusion.Fragment, "rFeatureIdManager", "DcFeatureIdManager"
    )
    Entries = MappingItems(Manager.Fields["featureIdMap"])
    Indices = {
        IntegerValue(Entry.First): IntegerValue(Entry.Second) for Entry in Entries
    }
    Allocated = tuple(
        Operation
        for Operation, Owner in Indices.items()
        if Owner == Extrusion.Extrude.ObjectId
    )
    Rounding = tuple(
        Operation
        for Operation, Owner in Indices.items()
        if Owner == Context.Feature.ObjectId
    )
    if (
        len(Indices) != len(Entries)
        or not BodyTag.PrimaryId.isdecimal()
        or len(Allocated) != 2
        or len(Rounding) != 1
    ):
        raise ValueError("Native rim requires explicit extrusion and fillet operations")
    Active = ReadSpanProgen(Graph, Extrusion, BodyTag, Allocated)
    if len(Active) != 1 or Active[0] not in Allocated or Rounding[0] in Allocated:
        raise ValueError("Native rim operations have inconsistent physical occurrences")
    return Active[0], Rounding[0]
