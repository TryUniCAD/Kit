from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimMap import ReadRimMap
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimDependencies import (
    RimDependencies,
)
from convert.adapters.Fusion.Native.Graph.GraphChecks import RequireFields
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph


# reciprocal maps alone cannot prove the selected edge belongs to the preceding extrusion
def CheckRimDeps(Graph: NativeGraph, Context: RimContext) -> None:
    Manager = Graph.OneClass("DcDependencyManager")
    RequireFields(Manager, {"mapsAreCurrent": True})
    Before = ReadRimMap(Manager.Fields["predecessorMap"])
    After = ReadRimMap(Manager.Fields["successorMap"])
    Forward = {
        (
            Graph.Resolve(First).Identity,
            Graph.Resolve(Second).Identity,
            IntegerValue(Flags),
        )
        for Second, Values in Before.items()
        for First, Flags in ReadRimMap(Values).items()
    }
    Backward = {
        (
            Graph.Resolve(First).Identity,
            Graph.Resolve(Second).Identity,
            IntegerValue(Flags),
        )
        for First, Values in After.items()
        for Second, Flags in ReadRimMap(Values).items()
    }
    if Forward != Backward or Forward != RimDependencies(Graph, Context):
        raise ValueError("Native rim dependency maps disagree with semantic owners")
