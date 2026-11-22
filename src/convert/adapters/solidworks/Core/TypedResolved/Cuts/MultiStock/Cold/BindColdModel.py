from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.BindExtrude import (
    BindDepth,
    BindExtrude,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.BindColdProfile import (
    BindColdProfile,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockOwners import (
    ColdStockOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckColdRows import (
    CheckColdRows,
)


# selected producer dependencies must follow the actual linked operation and datum identities
def BindColdModel(Model: NativeModel, OwnersValue: ColdStockOwners) -> NativeModel:
    LinkValue = OwnersValue.LinkValue
    Features = IndexFeatures(LinkValue)
    CheckColdRows(Model, LinkValue, Features)
    FirstStock, SecondStock = OwnersValue.StockValues
    CutValue = OwnersValue.CutValue
    OwnerValues = (FirstStock, SecondStock, CutValue)
    ByFeature = {NativeNodeId(Owner.NodeValue): Owner for Owner in OwnerValues}
    ByProfile = {NativeNodeId(Owner.ProfileValue): Owner for Owner in OwnerValues}
    if (
        tuple(Operation.object_id for Operation in Model.operations) != tuple(ByFeature)
        or set(ByProfile) != {Sketch.object_id for Sketch in Model.sketches}
        or any(
            tuple(Param.name for Param in Feature.dimensions)
            != (
                ("D1",)
                if Feature.object_id
                in (Model.operations[0].object_id, Model.operations[1].object_id)
                else ()
            )
            for Feature in Model.features
        )
        or any(
            Features[NativeId] is not Owner.NodeValue
            for NativeId, Owner in ByFeature.items()
        )
    ):
        raise ValueError(
            "public stock timeline conflicts with its actual linked owners"
        )
    First, Second, CutOperation = Model.operations
    Selected = OwnersValue.StockValues[OwnersValue.SelectedIndex]
    ProfileId = NativeNodeId(CutValue.ProfileValue)
    Scope = ReplaceValue(
        CutOperation,
        profile_id=ProfileId,
        dependencies=(NativeNodeId(Selected.NodeValue), ProfileId),
        length_mm=None,
        direction_code=1,
        termination_code=1,
        ThroughDirection=OwnersValue.ProfileFrames[2].z_axis,
    )
    return ReplaceValue(
        Model,
        features=tuple(
            (
                BindDepth(Feature, ByFeature[Feature.object_id])
                if Feature.object_id in ByFeature
                and Feature.object_id != CutOperation.object_id
                else Feature
            )
            for Feature in Model.features
        ),
        sketches=tuple(
            BindColdProfile(
                Sketch, ByProfile[Sketch.object_id], OwnersValue, Features, Model
            )
            for Sketch in Model.sketches
        ),
        operations=(
            BindExtrude(First, FirstStock),
            BindExtrude(Second, SecondStock),
            Scope,
        ),
    )
