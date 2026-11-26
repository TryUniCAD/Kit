from convert.adapters.Fusion.Native.FixedPrism.ReadSnapCaches import (
    ReadSnapCaches,
)
from convert.adapters.Fusion.Native.FixedPrism.ReadSnapOwner import (
    ReadSnapOwner,
)
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# ordered passive identities must select the solid region and sketch roots of this snapshot
def CheckFixedSnap(
    Graph: NativeGraph, Context: ExtrudeContext, Model: DocumentModel
) -> None:
    if len(Model.Snapshots) != 1 or not isinstance(
        Model.Snapshots[0].Snapshot, PrismSnapshot
    ):
        raise ValueError(
            "Native fixed cuboid requires exactly one typed prism snapshot"
        )
    Serializer = ReadSnapOwner(Graph, Context, Model.Snapshots[0].Name)
    Generator = ResolveField(
        Graph, Serializer, "topEntityPIDGenerator", "PassiveIdGenerator"
    )
    ToolNode, Region = ReadSnapCaches(Graph, Context, Model.Asset.AssetId)
    Owners = (
        IntegerValue(ToolNode.Fields["cachedEntityId"]),
        IntegerValue(Region.Fields["cachedEntityId"]),
        IntegerValue(Context.Sketch.Fields["bodyId"]),
    )
    ScanOrder = SeriesItems(Generator.Fields["scanOrderIndex"])
    Addresses = SeriesItems(Generator.Fields["addressOfTopEntities"])
    if (
        ScanOrder != Owners
        or len(set(Owners)) != 3
        or min(Owners) <= 0
        or IntegerValue(Generator.Fields["nextId"]) <= max(Owners)
        or len(Addresses) != len(Owners)
    ):
        raise ValueError(
            "Native fixed snapshot passive identities disagree with its roots"
        )
