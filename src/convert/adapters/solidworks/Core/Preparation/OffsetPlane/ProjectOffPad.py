from dataclasses import replace as ReplaceValue

from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# the single joined native result is the neutral first creator with the exact owned depth
def ProjectOffPad(
    BossStep: FeatureStep, DatumId: str, Display: Parameter, Depth: Parameter
) -> FeatureStep:
    Definition = BossStep.definition
    if type(Definition) is not ExtrudeFeature or Definition.length != Display.value:
        raise ValueError("SOLIDWORKS offset readback boss and D1 disagree")
    return ReplaceValue(
        BossStep,
        order=1,
        operation=BooleanOp.KCreate,
        definition=ReplaceValue(Definition, length=Depth.value),
        input_feature_ids=(DatumId,),
        selection_ids=(),
        provenance=None,
        attributes=FreezeMapping(),
    )
