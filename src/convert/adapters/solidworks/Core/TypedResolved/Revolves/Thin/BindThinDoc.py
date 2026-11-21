from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.CheckRevSupport import (
    CheckRevSupport,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.MakeRevSelect import (
    MakeRevSelect,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.BindThinParams import (
    BindThinParams,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.BindThinSketch import (
    BindThinSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.BindThinStep import (
    BindThinStep,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinRevOwner import (
    ThinRevOwner,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# no thin definition is projected until its neutral feature and body owners are identified together
def BindThinDoc(
    Document: CadDocument, LinkValue: NativeLink, OwnerValue: ThinRevOwner
) -> CadDocument:
    SweepValue = OwnerValue.SweepValue
    FeatureId = f"sldprt:feature:{NativeNodeId(SweepValue.NodeValue)}"
    SketchId = f"sldprt:sketch:{NativeNodeId(SweepValue.ProfileValue)}"
    (StepValue,) = (
        Value for Value in Document.feature_timeline if Value.id == FeatureId
    )
    (SketchValue,) = Document.sketches
    (BodyValue,) = Document.bodies
    NameValue = ReadNativeName(SweepValue.NodeValue)
    if (
        SketchValue.id != SketchId
        or SketchValue.suppressed
        or StepValue.suppressed
        or StepValue.configuration_states
        or StepValue.name != NameValue
        or BodyValue.name not in ("Body 1", NameValue)
    ):
        raise ValueError("SOLIDWORKS thin neutral feature and sketch ownership differ")
    CheckRevSupport(Document, SketchValue, SweepValue)
    SelectValue = MakeRevSelect(LinkValue, SweepValue)
    if any(Value.id == SelectValue.id for Value in Document.selections):
        raise ValueError("SOLIDWORKS thin native axis overlaps a prior selection")
    ParamValues, ParamIds = BindThinParams(Document.parameters, LinkValue, OwnerValue)
    BoundStep = BindThinStep(StepValue, LinkValue, OwnerValue, SelectValue, ParamIds)
    return ReplaceValue(
        Document,
        sketches=(BindThinSketch(SketchValue, SweepValue),),
        selections=(*Document.selections, SelectValue),
        parameters=ParamValues,
        feature_timeline=tuple(
            BoundStep if Value is StepValue else Value
            for Value in Document.feature_timeline
        ),
        bodies=(
            ReplaceValue(
                BodyValue,
                name=NameValue,
                final_feature_id=FeatureId,
                provenance=BoundStep.provenance,
            ),
        ),
        metadata=FreezeMapping(
            {**Document.metadata, "solidworks.typed_thin_revolve_semantics": True}
        ),
    )
