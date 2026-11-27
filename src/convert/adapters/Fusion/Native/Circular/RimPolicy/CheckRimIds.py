from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimMap import ReadRimMap
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import EmptyFields
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph


# operation allocation must identify the actual three source features rather than arbitrary live labels
def CheckRimIds(Graph: NativeGraph, Context: RimContext) -> None:
    Manager = Graph.OneClass("DcFeatureIdManager")
    EmptyFields(Manager, ("obsoleteFeatureIds",))
    Identities = ReadRimMap(Manager.Fields["featureIdMap"])
    Inverse = ReadRimMap(Manager.Fields["enetityIdMap"])
    Features = (
        Context.Extrusion.SketchFeature,
        Context.Extrusion.Extrude,
        Context.Feature,
    )
    if (
        set(IntegerValue(Value) for Value in Identities.values())
        != {Value.ObjectId for Value in Features}
        or len(Identities) != 4
        or len(Inverse) != 3
    ):
        raise ValueError(
            "Native rim feature allocation omits or adds an operation owner"
        )
    if {
        (IntegerValue(First), IntegerValue(Second))
        for First, Second in Identities.items()
    } != {
        (IntegerValue(Second), IntegerValue(First))
        for First, Values in Inverse.items()
        for Second in SeriesItems(Values)
    }:
        raise ValueError("Native rim feature allocation maps are not reciprocal")
    if (
        len(SeriesItems(Inverse[Context.Extrusion.Extrude.ObjectId])) != 2
        or len(SeriesItems(Inverse[Context.Extrusion.SketchFeature.ObjectId])) != 1
        or len(SeriesItems(Inverse[Context.Feature.ObjectId])) != 1
    ):
        raise ValueError(
            "Native rim feature allocation has unsupported operation roles"
        )
