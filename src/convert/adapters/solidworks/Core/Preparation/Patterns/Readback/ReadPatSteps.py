from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Patterns.Readback.ReadPatLength import (
    ReadPatLength,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureKinds import LinearPattern
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.Records.RecordParameter import Parameter


# the body pick follows the already checked predecessor instead of a native axis marker
def PatBodyPick(StepValue: FeatureStep, Previous: FeatureStep) -> Selection:
    return Selection(
        f"{StepValue.id}:body-pick",
        Previous.name,
        (SelectPathElem("feature", Previous.id, "body"),),
    )


# an archive join on empty history becomes the neutral create operation
def ProjectPatStock(
    StepValue: FeatureStep,
    Drivers: dict[str, Parameter],
    Previous: FeatureStep | None,
) -> tuple[FeatureStep, Parameter, Selection | None]:
    Definition = StepValue.definition
    (DepthId,) = StepValue.parameter_ids
    DriverValue = Drivers[DepthId]
    if type(Definition) is not ExtrudeFeature or Definition.length != DriverValue.value:
        raise ValueError("SOLIDWORKS cold pattern stock differs from its driving depth")
    DepthValue = ReadPatLength(DriverValue, StepValue.id, "D1")
    PickValue = PatBodyPick(StepValue, Previous) if Previous is not None else None
    return (
        ReplaceValue(
            StepValue,
            definition=ReplaceValue(Definition, length=DepthValue.value),
            operation=BooleanOp.KCreate if Previous is None else BooleanOp.KJoin,
            input_feature_ids=(Previous.id,) if Previous is not None else (),
            selection_ids=(PickValue.id,) if PickValue is not None else (),
            provenance=None,
            attributes=FreezeMapping(),
        ),
        DepthValue,
        PickValue,
    )


# pitch and seed both come from the measured typed pattern dependencies
def ProjectPatStep(
    StepValue: FeatureStep, SeedValue: FeatureStep, Drivers: dict[str, Parameter]
) -> tuple[FeatureStep, Parameter, Selection]:
    Definition = StepValue.definition
    _, PitchId = StepValue.parameter_ids
    DriverValue = Drivers[PitchId]
    if type(Definition) is not LinearPattern or Definition.spacing != DriverValue.value:
        raise ValueError("SOLIDWORKS cold pattern differs from its driving pitch")
    PitchValue = ReadPatLength(DriverValue, StepValue.id, "D3")
    PickValue = PatBodyPick(StepValue, SeedValue)
    return (
        ReplaceValue(
            StepValue,
            definition=ReplaceValue(Definition, spacing=PitchValue.value),
            operation=BooleanOp.KJoin,
            selection_ids=(*StepValue.selection_ids, PickValue.id),
            provenance=None,
            attributes=FreezeMapping(),
        ),
        PitchValue,
        PickValue,
    )
