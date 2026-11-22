from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import DecodeNotices, NativeModel
from convert.adapters.solidworks.Core.TypedResolved.BindExtrude import (
    BindDepth,
    BindExtrude,
)
from convert.adapters.solidworks.Core.TypedResolved.BindFeature import BindFeature
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Shells.ShellPartRead import (
    ShellPartRead,
)


# bound features keep public identities and replace any heuristic shell selection with typed owners
def BindShellModel(ModelValue: NativeModel, ReadValue: ShellPartRead) -> NativeModel:
    StockOwner = ReadValue.StockValue.OwnerValue
    StockNode, ShellNode = StockOwner.NodeValue, ReadValue.ShellNode
    StockId, ShellId = NativeNodeId(StockNode), NativeNodeId(ShellNode)
    StockOp, ShellOp = ModelValue.operations
    (SketchValue,) = ModelValue.sketches
    if (
        (StockOp.object_id, ShellOp.object_id) != (StockId, ShellId)
        or SketchValue.object_id != NativeNodeId(StockOwner.ProfileValue)
        or SketchValue.support_plane_id != ReadValue.StockValue.PlaneId
    ):
        raise ValueError(
            "SOLIDWORKS shell archive disagrees with the selected public history"
        )
    if ReadValue.FreshRoots and (
        StockOp.profile_id != SketchValue.object_id
        or ShellOp.dependencies != (StockId,)
    ):
        raise ValueError(
            "fresh shell public dependencies differ from the linked owners"
        )
    NativeFeatures = {Value.object_id: Value for Value in ModelValue.features}
    BoundFeatures = {
        NativeNodeId(NodeValue): BindFeature(
            NativeFeatures[NativeNodeId(NodeValue)], NodeValue, ReadValue.LinkValue
        )
        for NodeValue in (ReadValue.FreshRoots or (StockNode, ShellNode))
    }
    StockFeature, ShellFeature = BoundFeatures[StockId], BoundFeatures[ShellId]
    if any(
        tuple(Value.name for Value in Feature.dimensions) != ("D1",)
        for Feature in (StockFeature, ShellFeature)
    ):
        raise ValueError(
            "SOLIDWORKS shell needs its actual two independent public drivers"
        )
    BoundFeatures[StockId] = BindDepth(StockFeature, StockOwner)
    BoundFeatures[ShellId] = ReplaceValue(
        ShellFeature, dimensions=(ReadValue.DriverValue.DepthValue,)
    )
    UpdatedShell = ReplaceValue(
        ShellOp,
        profile_id=None,
        dependencies=(StockId,),
        length_mm=ReadValue.DriverValue.DepthValue.value_mm,
        selection_offsets=(),
        selected_local_ids=(),
        selection_references=(),
    )
    SketchValue = ReplaceValue(
        SketchValue,
        name=ReadNativeName(StockOwner.ProfileValue),
        TypedLines=ReadValue.StockValue.LoopValue,
    )
    StockOp = BindExtrude(StockOp, StockOwner)
    NameNotices = (
        DecodeNotices(ModelValue.features, (), ()) if ReadValue.FreshRoots else ()
    )
    PriorNotice = "typed resolved semantics unavailable: unsupported SOLIDWORKS body class moShell_c schema 1"
    return ReplaceValue(
        ModelValue,
        features=(
            tuple(BoundFeatures.values())
            if ReadValue.FreshRoots
            else tuple(
                BoundFeatures.get(Value.object_id, Value)
                for Value in ModelValue.features
            )
        ),
        diagnostics=(
            tuple(
                Message
                for Message in ModelValue.diagnostics
                if Message not in NameNotices and Message != PriorNotice
            )
        ),
        operations=(StockOp, UpdatedShell),
        sketches=(SketchValue,),
    )
