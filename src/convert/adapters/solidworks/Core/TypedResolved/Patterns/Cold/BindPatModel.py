from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import NativeModel, NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.BindExtrude import (
    BindDepth,
    BindExtrude,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ColdPatPart import (
    ColdPatPart,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.PatStock import (
    PatStock,
)


# exact resolved stock owners replace only the matching public sketch and depth records
def BindPatSketch(SketchValue: NativeSketch, StockValue: PatStock) -> NativeSketch:
    return ReplaceValue(
        SketchValue,
        TypedLines=StockValue.LoopValue,
        TypedFrame=StockValue.PlanValue.FrameValue,
        dimensions=(),
        constraints=(),
    )


# stock binding follows the actual plate and seed profiles without changing generic native fallback
def BindPatModel(ModelValue: NativeModel, PatternValue: ColdPatPart) -> NativeModel:
    StocksValue = PatternValue.StocksValue
    ProfileMap = {
        NativeNodeId(Value.OwnerValue.ProfileValue): Value for Value in StocksValue
    }
    FeatureMap = {
        NativeNodeId(Value.OwnerValue.NodeValue): Value.OwnerValue
        for Value in StocksValue
    }
    if set(ProfileMap) != {Value.object_id for Value in ModelValue.sketches}:
        raise ValueError("cold pattern stock profiles disagree with the keyword index")
    return ReplaceValue(
        ModelValue,
        sketches=tuple(
            BindPatSketch(Value, ProfileMap[Value.object_id])
            for Value in ModelValue.sketches
        ),
        features=tuple(
            (
                BindDepth(Value, FeatureMap[Value.object_id])
                if Value.object_id in FeatureMap
                else Value
            )
            for Value in ModelValue.features
        ),
        operations=tuple(
            (
                BindExtrude(Value, FeatureMap[Value.object_id])
                if Value.object_id in FeatureMap
                else Value
            )
            for Value in ModelValue.operations
        ),
    )
