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
    if OwnerValue.ModeValue == ExtrudeEnd.KThroughAll:
        return ReplaceValue(Feature, dimensions=())
    DepthValues: tuple[NativeDimension, ...] = (OwnerValue.RequireDepth().DepthValue,)
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
    Termination = {ExtrudeEnd.KThroughAll: 1, ExtrudeEnd.KMidPlane: 6}
    return ReplaceValue(
        Operation,
        profile_id=ProfileId,
        dependencies=ParentIds,
        length_mm=(
            None
            if OwnerValue.DepthValue is None
            else OwnerValue.DepthValue.DepthValue.value_mm
        ),
        direction_code=int(OwnerValue.IsReversed),
        termination_code=Termination.get(OwnerValue.ModeValue, 0),
        second_length_mm=(
            None
            if OwnerValue.SecondValue is None
            else OwnerValue.SecondValue.DepthValue.value_mm
        ),
        extrusion_end=OwnerValue.ModeValue,
        second_extrusion_end=OwnerValue.SecondModeValue,
    )
