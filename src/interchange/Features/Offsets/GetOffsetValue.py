from typing import Mapping as TypeMap

from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.DistanceParam import GetDistParam
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Offsets.FaceOffset import FaceOffset
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.Records.RecordParameter import Parameter


# offset evaluation uses the original face direction and an owned signed length without changing the pick
def GetOffsetValue(
    Feature: FeatureStep,
    Definition: FaceOffset,
    Parameters: TypeMap[str, Parameter],
    Selections: TypeMap[str, Selection],
) -> float:
    if Feature.kind != FeatureKind.KOffset or Feature.operation is not None:
        raise ValueError(
            "face offset requires an offset feature without boolean operation"
        )
    if Feature.sketch_id is not None or Feature.OutputBodyIds != (
        Definition.TargetBodyId,
    ):
        raise ValueError("face offset must modify its declared target body")
    Selected = Selections.get(Definition.FaceSelectionId)
    if (
        Feature.selection_ids != (Definition.FaceSelectionId,)
        or Selected is None
        or len(Selected.path) != 2
        or Selected.path[0] != SelectPathElem("body", Definition.TargetBodyId)
        or Selected.path[1].entity_kind != "face"
        or not Selected.path[1].entity_id
        or Selected.path[1].subelement
    ):
        raise ValueError(
            "face offset requires one explicit face selection on its target body"
        )
    return GetDistParam(
        Feature, Definition.DistanceParamId, Parameters, ValueKind.KLength
    )
