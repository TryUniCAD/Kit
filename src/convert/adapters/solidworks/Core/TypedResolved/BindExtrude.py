from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import (
    NativeDimension,
    NativeFeature,
    NativeOperation,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from interchange.Features.FeatureExtrude import ExtrudeEnd


# actual active end depths replace same named keyword values while preserving other unrelated dimensions
def BindDepth(Feature: NativeFeature, OwnerValue: ExtrudeOwner) -> NativeFeature:
    DepthValues: tuple[NativeDimension, ...] = (OwnerValue.DepthValue.DepthValue,)
    if OwnerValue.SecondValue is not None:
        DepthValues = (*DepthValues, OwnerValue.SecondValue.DepthValue)
    NamesValue = {Dimension.name for Dimension in DepthValues}
    OtherValues = tuple(
        Dimension
        for Dimension in Feature.dimensions
        if Dimension.name not in NamesValue
    )
    return ReplaceValue(Feature, dimensions=(*DepthValues, *OtherValues))


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
        termination_code=6 if OwnerValue.ModeValue == ExtrudeEnd.KMidPlane else 0,
        second_length_mm=(
            None
            if OwnerValue.SecondValue is None
            else OwnerValue.SecondValue.DepthValue.value_mm
        ),
        extrusion_end=OwnerValue.ModeValue,
    )
