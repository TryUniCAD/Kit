from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.BindExtrude import (
    BindDepth,
    BindExtrude,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.EllipPartRead import (
    EllipPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# complete linked feature names and the active depth replace only the corresponding legacy observations
def BindEllipModel(ModelValue: NativeModel, PartValue: EllipPartRead) -> NativeModel:
    BossValue = PartValue.BossValue
    BossId = NativeNodeId(BossValue.NodeValue)
    Names = {
        NativeId: ReadNativeName(NodeValue)
        for NativeId, NodeValue in IndexFeatures(PartValue.LinkValue).items()
    }
    Features = tuple(
        ReplaceValue(
            BindDepth(Value, BossValue) if Value.object_id == BossId else Value,
            name=Names[Value.object_id],
        )
        for Value in ModelValue.features
    )
    ResolvedNames = {
        f"native name records unavailable for {NativeId}:{NameValue}"
        for NativeId, NameValue in Names.items()
    }
    (Operation,) = ModelValue.operations
    (Sketch,) = ModelValue.sketches
    return ReplaceValue(
        ModelValue,
        features=Features,
        sketches=(ReplaceValue(Sketch, name=Names[Sketch.object_id]),),
        operations=(
            ReplaceValue(BindExtrude(Operation, BossValue), name=Names[BossId]),
        ),
        diagnostics=tuple(
            Value for Value in ModelValue.diagnostics if Value not in ResolvedNames
        ),
    )
