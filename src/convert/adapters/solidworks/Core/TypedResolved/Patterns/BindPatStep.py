from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternOwner import (
    PatternOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureKinds import LinearPattern
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.Records.RecordParameter import Parameter


# seed and datum identities must replace the heuristic dependency and selection query together
def BindPatStep(
    StepValue: FeatureStep,
    OwnerValue: PatternOwner,
    LinkValue: NativeLink,
    SelectValue: Selection,
    CountValue: Parameter,
    PitchValue: Parameter,
) -> FeatureStep:
    NativeId = NativeNodeId(OwnerValue.NodeValue)
    SeedId = NativeNodeId(OwnerValue.SeedValue)
    PlaneId = NativeNodeId(OwnerValue.DatumValue.PlaneValue)
    Count = CountValue.value.value
    if type(Count) is not int:
        raise ValueError("pattern has no integral neutral count")
    ProofValue = NativeNodeSpan(LinkValue, OwnerValue.NodeValue)
    Attributes = dict(StepValue.attributes)
    for NameValue in (
        "native_selection_offsets",
        "selected_local_ids",
        "native_selection_references",
    ):
        Attributes.pop(NameValue, None)
    return ReplaceValue(
        StepValue,
        input_feature_ids=(f"sldprt:feature:{SeedId}", f"sldprt:feature:{PlaneId}"),
        selection_ids=(SelectValue.id,),
        definition=LinearPattern(
            PitchValue.value, Count, SelectValue.id, OwnerValue.DatumValue.ReversedValue
        ),
        provenance=TypedProvenance(ProofValue, str(NativeId)),
        attributes=FreezeMapping(
            {
                **Attributes,
                "native_dependencies": (SeedId, PlaneId),
                "selection_kind": "support_plane",
                "direction_code": int(OwnerValue.DatumValue.ReversedValue),
                "typed_archive_owner": ProofValue,
            }
        ),
    )
