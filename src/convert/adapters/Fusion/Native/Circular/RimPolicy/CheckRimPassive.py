from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    RequireFields,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph


# passive allocators must cover their own positive identities without treating saved memory addresses as generated values
def CheckRimPassive(Graph: NativeGraph, Context: RimContext) -> None:
    for Value in Graph.ByClass("PassiveIdGenerator"):
        ScanOrder = tuple(
            IntegerValue(Entry) for Entry in SeriesItems(Value.Fields["scanOrderIndex"])
        )
        Addresses = tuple(
            IntegerValue(Entry)
            for Entry in SeriesItems(Value.Fields["addressOfTopEntities"])
        )
        if (
            not ScanOrder
            or len(set(ScanOrder)) != len(ScanOrder)
            or min(ScanOrder) <= 0
            or IntegerValue(Value.Fields["nextId"]) <= max(ScanOrder)
        ):
            raise ValueError(
                "Native rim passive allocator does not bound its owned identities"
            )
        if Addresses and (len(Addresses) != len(ScanOrder) or min(Addresses) <= 0):
            raise ValueError("Native rim passive addresses disagree with their scan")
        RequireFields(Value, {"rBody": None})
        if Value.Fields["rBodies"] is not None and Graph.Resolve(
            Value.Fields["rBodies"]
        ) != Graph.Resolve(Context.Extrusion.Component.Fields["rBodies"]):
            raise ValueError(
                "Native rim passive allocator belongs to another body collection"
            )
    Serializer = Graph.OneClass("BRepSerializer")
    Generator = ResolveField(
        Graph, Serializer, "topEntityPIDGenerator", "PassiveIdGenerator"
    )
    RequireFields(Generator, {"rBodies": None})
    RequireFields(Serializer, {"rBody": None})
    EmptyFields(Serializer, ("mapBodyId",))
