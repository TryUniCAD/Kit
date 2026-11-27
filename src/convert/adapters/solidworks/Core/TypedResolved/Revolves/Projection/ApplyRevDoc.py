from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import KDirectionAxisRole

from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.BindRevParams import (
    BindRevParams,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.BindRevStep import (
    BindRevStep,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.CheckRevSupport import (
    CheckRevSupport,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.MakeRevSelect import (
    MakeRevSelect,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.MakeRevSketch import (
    MakeRevSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.ReportRevolve import (
    ReportRevolve,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# the public model must replace all linked revolve semantics together while preserving unrelated source records
def ApplyRevDoc(
    DocumentValue: CadDocument, LinkValue: NativeLink, OwnerValue: RevolveOwner
) -> CadDocument:
    FeatureId = f"sldprt:feature:{NativeNodeId(OwnerValue.NodeValue)}"
    SketchId = f"sldprt:sketch:{NativeNodeId(OwnerValue.ProfileValue)}"
    StepValues = tuple(
        Value for Value in DocumentValue.feature_timeline if Value.id == FeatureId
    )
    SketchValues = tuple(
        Value for Value in DocumentValue.sketches if Value.id == SketchId
    )
    if len(StepValues) != 1 or len(SketchValues) != 1:
        raise ValueError(
            "ordinary revolve lacks its real public feature or consumed sketch"
        )
    if StepValues[0].suppressed or StepValues[0].configuration_states:
        raise ValueError(
            "ordinary revolve neutral suppression state is outside measured semantics"
        )
    CheckRevSupport(DocumentValue, SketchValues[0], OwnerValue)
    SketchValue = MakeRevSketch(SketchValues[0], OwnerValue)
    ParamValues, ParamIds = BindRevParams(DocumentValue.parameters, OwnerValue)
    SelectValue = MakeRevSelect(LinkValue, OwnerValue)
    StepValue = BindRevStep(StepValues[0], OwnerValue, LinkValue, SelectValue, ParamIds)
    SelectValues = tuple(
        Value
        for Value in DocumentValue.selections
        if not (
            Value.query.get("native_owner_id") == NativeNodeId(OwnerValue.NodeValue)
            and Value.query.get("topology_role") == KDirectionAxisRole
        )
    )
    if any(Value.id == SelectValue.id for Value in SelectValues):
        raise ValueError(
            "ordinary revolve selected axis identity conflicts with an existing neutral selection"
        )
    return ReplaceValue(
        DocumentValue,
        sketches=tuple(
            SketchValue if Value.id == SketchId else Value
            for Value in DocumentValue.sketches
        ),
        parameters=ParamValues,
        selections=(*SelectValues, SelectValue),
        feature_timeline=tuple(
            StepValue if Value.id == FeatureId else Value
            for Value in DocumentValue.feature_timeline
        ),
        metadata=FreezeMapping(
            {
                **DocumentValue.metadata,
                "solidworks.typed_revolve_semantics": {
                    "status": "projected",
                    "revolutions": (ReportRevolve(LinkValue, OwnerValue),),
                    "typed_geometry_projection": True,
                    "full_document_qualified": False,
                    "public_writer_qualified": False,
                },
            }
        ),
    )
