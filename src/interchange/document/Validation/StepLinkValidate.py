from typing import Mapping as TypeMap

from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.SweepFeature import SweepFeature
from interchange.document.Validation.SweepValidate import GetSweepErrs
from interchange.geometry.Models.Sketch import Sketch


# step links must name an existing entity and point only to prior operations
def GetStepErrors(
    FeatureValue: FeatureStep,
    FeatureOrders: TypeMap[str, int],
    IdentitySets: TypeMap[str, set[str]],
    Sketches: TypeMap[str, Sketch],
) -> list[str]:
    ErrorValues: list[str] = []
    if (
        FeatureValue.sketch_id
        and FeatureValue.sketch_id not in IdentitySets["sketches"]
    ):
        ErrorValues.append(f"feature {FeatureValue.id} references missing sketch")
    for InputId in FeatureValue.input_feature_ids:
        if InputId not in FeatureOrders:
            ErrorValues.append(
                f"feature {FeatureValue.id} references missing input {InputId}"
            )
        elif FeatureOrders[InputId] >= FeatureValue.order:
            ErrorValues.append(f"feature {FeatureValue.id} has a forward dependency")
    for ParameterId in FeatureValue.parameter_ids:
        if ParameterId not in IdentitySets["parameters"]:
            ErrorValues.append(
                f"feature {FeatureValue.id} references missing parameter"
            )
    for SelectionId in FeatureValue.selection_ids:
        if SelectionId not in IdentitySets["selections"]:
            ErrorValues.append(
                f"feature {FeatureValue.id} references missing selection"
            )
    Definition = FeatureValue.definition
    if isinstance(Definition, SweepFeature):
        ErrorValues.extend(GetSweepErrs(FeatureValue, Definition, Sketches))
    return ErrorValues
