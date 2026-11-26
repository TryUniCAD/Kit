from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import NativeFeature, NativeOperation
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# only the owned forward depth replaces matching keyword dimensions without dropping unrelated legacy parameters
def BindDepth(Feature: NativeFeature, OwnerValue: ExtrudeOwner) -> NativeFeature:
    DepthValue = OwnerValue.DepthValue.DepthValue
    OtherValues = tuple(
        Dimension
        for Dimension in Feature.dimensions
        if Dimension.name != DepthValue.name
    )
    return ReplaceValue(Feature, dimensions=(DepthValue, *OtherValues))


# the measured single boss must follow actual typed parents rather than stale keyword dependencies
def BindExtrude(
    Operation: NativeOperation, OwnerValue: ExtrudeOwner
) -> NativeOperation:
    ProfileId = NativeNodeId(OwnerValue.ProfileValue)
    ParentIds = tuple(NativeNodeId(NodeValue) for NodeValue in OwnerValue.ParentsValue)
    return ReplaceValue(
        Operation,
        profile_id=ProfileId,
        dependencies=ParentIds,
        length_mm=OwnerValue.DepthValue.DepthValue.value_mm,
        direction_code=int(OwnerValue.IsReversed),
        termination_code=0,
    )
