from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ExactMm import ExactMm
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# the editable feature and its only depth driver must use the same normalized wire length
def ReadColdBoss(
    Feature: FeatureStep, Driver: Parameter
) -> tuple[FeatureStep, Parameter]:
    Definition = Feature.definition
    Display = Driver.value.value
    if (
        type(Definition) is not ExtrudeFeature
        or Feature.parameter_ids != (Driver.id,)
        or Driver.attributes.get("native_unit") != "m"
        or Driver.value.unit != "mm"
        or Definition.length != Driver.value
        or type(Display) is not float
    ):
        raise ValueError("SOLIDWORKS cold boss requires its exact typed D1")
    DepthValue = ReplaceValue(
        Driver.value,
        value=ExactMm(Driver.attributes.get("native_value"), Display),
    )
    return (
        ReplaceValue(
            Feature,
            order=0,
            definition=ReplaceValue(Definition, length=DepthValue),
            selection_ids=(),
            input_feature_ids=(),
            attributes=FreezeMapping(),
            provenance=None,
        ),
        ReplaceValue(
            Driver, value=DepthValue, attributes=FreezeMapping(), provenance=None
        ),
    )
