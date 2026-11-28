from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeFeature, NativeModel
from convert.adapters.solidworks.Core.TypedResolved.BindExtrude import BindDepth
from convert.adapters.solidworks.Core.TypedResolved.BindFeature import BindFeature
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.OrderWarmDims import (
    OrderWarmDims,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# bind the actual stock depth and align angle presentation with the joined live slots
def BindChmfRoots(
    ModelValue: NativeModel, PartValue: ChmfPartRead, Nodes: Mapping[int, ArchiveNode]
) -> dict[int, NativeFeature]:
    Public = {Value.object_id: Value for Value in ModelValue.features}
    Features = {
        NativeId: BindFeature(Public[NativeId], Value, PartValue.LinkValue)
        for NativeId, Value in Nodes.items()
    }
    StockId = NativeNodeId(PartValue.StockValue.NodeValue)
    Features[StockId] = BindDepth(Features[StockId], PartValue.StockValue)
    Owners = PartValue.OwnersValue
    if PartValue.WarmValue is not None and Owners.ModeWord == 1:
        ChmfId = NativeNodeId(Owners.FeatureValue)
        Feature = Features[ChmfId]
        Features[ChmfId] = ReplaceValue(
            Feature, dimensions=OrderWarmDims(Feature.dimensions, Owners)
        )
    return Features
