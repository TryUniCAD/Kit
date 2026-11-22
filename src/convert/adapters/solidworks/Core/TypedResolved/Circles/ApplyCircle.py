from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import NativeModel, NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.BindExtrude import (
    BindDepth,
    BindExtrude,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner


# both public dimension owners and the actual model timeline publish one atomic typed update
def ApplyCircle(
    ModelValue: NativeModel, SketchValue: NativeSketch, Owner: ExtrudeOwner
) -> NativeModel:
    (Operation,) = ModelValue.operations
    return ReplaceValue(
        ModelValue,
        sketches=(SketchValue,),
        features=tuple(
            (
                BindDepth(Feature, Owner)
                if Feature.object_id == Operation.object_id
                else (
                    ReplaceValue(Feature, dimensions=SketchValue.dimensions)
                    if Feature.object_id == SketchValue.object_id
                    else Feature
                )
            )
            for Feature in ModelValue.features
        ),
        operations=(BindExtrude(Operation, Owner),),
    )
