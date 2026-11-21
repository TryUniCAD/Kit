from typing import Mapping as TypeMap

from interchange.document.Models.DocumentModel import (  # lgtm[py/cyclic-import]
    CadDocument,
)
from interchange.document.Validation.DocumentDefValidate import GetDefErrors
from interchange.Features.Axes.AxisExtentConfig import MakeAxisView
from interchange.Features.Axes.BoundPlaneAxis import BoundPlaneAxis
from interchange.Features.FeatureStep import FeatureStep


# step links must name an existing entity and point only to prior operations
def GetStepErrors(
    FeatureValue: FeatureStep,
    FeatureOrders: TypeMap[str, int],
    IdentitySets: TypeMap[str, set[str]],
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
    return ErrorValues


# timeline checks protect ordering and every feature dependency from invalid references
def GetFeatureErrs(
    DocumentValue: CadDocument, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    FeatureOrders = {
        FeatureValue.id: FeatureValue.order
        for FeatureValue in DocumentValue.feature_timeline
    }
    if len(FeatureOrders) != len(DocumentValue.feature_timeline):
        ErrorValues.append("feature ids are not unique")
    if len(
        {FeatureValue.order for FeatureValue in DocumentValue.feature_timeline}
    ) != len(DocumentValue.feature_timeline):
        ErrorValues.append("feature order values are not unique")
    Selections = {Value.id: Value for Value in DocumentValue.selections}
    Parameters = {Value.id: Value for Value in DocumentValue.parameters}
    Frames = {Value.id: Value for Value in DocumentValue.support_planes}
    Sketches = {Value.id: Value for Value in DocumentValue.sketches}
    AxisView = (
        MakeAxisView(DocumentValue.configurations)
        if any(
            isinstance(FeatureValue.definition, BoundPlaneAxis)
            for FeatureValue in DocumentValue.feature_timeline
        )
        else None
    )
    for FeatureValue in DocumentValue.feature_timeline:
        ErrorValues.extend(GetStepErrors(FeatureValue, FeatureOrders, IdentitySets))
        ErrorValues.extend(
            GetDefErrors(
                FeatureValue,
                IdentitySets,
                Selections,
                Parameters,
                Frames,
                Sketches,
                AxisView,
            )
        )
    for BodyValue in DocumentValue.bodies:
        if BodyValue.final_feature_id not in IdentitySets["feature_timeline"]:
            ErrorValues.append(f"body {BodyValue.id} references missing final feature")
    return tuple(ErrorValues)
