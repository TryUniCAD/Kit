from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletHistory import (
    FilletHistory,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.BindFilletParam import (
    BindFilletParam,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.BindFilletPick import (
    BindFilletPick,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.FilletEdge import (
    FilletEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletStep import (
    ReadFilletStep,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureKinds import FilletFeature
from interchange.Records.RecordTopology import TopologyCounts


# only the proved feature and its immediate owners are enriched during saved readback
def BindFilletModel(
    Document: CadDocument,
    History: FilletHistory,
    EdgeValue: FilletEdge,
    Topology: TopologyCounts,
    Centroid: tuple[float, ...],
) -> CadDocument:
    StockValue, StepValue = ReadFilletStep(Document, History)
    (BodyValue,) = Document.bodies
    (ParamId,) = StepValue.parameter_ids
    (PickId,) = StepValue.selection_ids
    if BodyValue.final_feature_id != StepValue.id:
        raise ValueError("saved fillet must own the public final body")
    (ParamValue,) = (
        Value
        for Value in Document.parameters
        if Value.owner_id == StepValue.id and Value.id == ParamId
    )
    (PickValue,) = (Value for Value in Document.selections if Value.id == PickId)
    Driver = BindFilletParam(ParamValue, History)
    PickedEdge = BindFilletPick(PickValue, StockValue.id, EdgeValue, History)
    ProvenanceValue = TypedProvenance(
        NativeNodeSpan(History.LinkValue, History.OwnersValue.FilletValue), StepValue.id
    )
    return ReplaceValue(
        Document,
        parameters=tuple(
            Driver if Value is ParamValue else Value for Value in Document.parameters
        ),
        selections=tuple(
            PickedEdge if Value is PickValue else Value for Value in Document.selections
        ),
        feature_timeline=tuple(
            (
                ReplaceValue(
                    Value,
                    definition=FilletFeature(Driver.value),
                    provenance=ProvenanceValue,
                )
                if Value is StepValue
                else Value
            )
            for Value in Document.feature_timeline
        ),
        bodies=(
            ReplaceValue(
                BodyValue,
                name=StepValue.name,
                topology=Topology,
                provenance=ProvenanceValue,
                attributes=FreezeMapping(
                    {**BodyValue.attributes, "solidworks.body_centroid_mm": Centroid}
                ),
            ),
        ),
        metadata=FreezeMapping(
            {**Document.metadata, "solidworks.typed_saved_edge_fillet": True}
        ),
    )
