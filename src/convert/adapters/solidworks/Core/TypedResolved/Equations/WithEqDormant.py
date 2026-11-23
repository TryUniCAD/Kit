from collections.abc import Callable
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Equations.WidthDepthLink import (
    WidthDepthLink,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.document.Models.DocumentModel import CadDocument


# the dormant native display belongs to the real one direction feature as a stored length
def WithEqDormant(
    DocumentValue: CadDocument,
    RelationValue: WidthDepthLink | None,
    MakeParamId: Callable[[int, str], str],
) -> CadDocument:
    if RelationValue is None or RelationValue.DormantValue is None:
        return DocumentValue
    Dormant = RelationValue.DormantValue.DepthValue
    (BossValue,) = (
        StepValue
        for StepValue in DocumentValue.feature_timeline
        if StepValue.attributes.get("native_object_id") == RelationValue.DepthFeature
    )
    Definition = BossValue.definition
    DriverId = MakeParamId(RelationValue.DepthFeature, RelationValue.DepthParam)
    DormantId = MakeParamId(RelationValue.DepthFeature, Dormant.name)
    if (
        type(Definition) is not ExtrudeFeature
        or Definition.end_condition != ExtrudeEnd.KBlind
        or Definition.second_length is not None
        or Definition.second_end_condition is not None
        or Definition.reversed
        or Definition.symmetric
        or BossValue.parameter_ids != (DriverId,)
        or Dormant.value_mm is None
        or any(RowValue.id == DormantId for RowValue in DocumentValue.parameters)
    ):
        raise ValueError("owned dormant depth requires the actual one direction boss")
    LengthValue = ParameterValue(Dormant.value_mm, ValueKind.KLength, "mm")
    DormantValue = Parameter(
        id=DormantId,
        name=Dormant.name,
        value=LengthValue,
        owner_id=BossValue.id,
        provenance=TypedProvenance(
            Dormant.TypedOwner, f"{RelationValue.DepthFeature}:{Dormant.name}"
        ),
        attributes={
            "native_role": "dormant",
            "typed_archive_owner": Dormant.TypedOwner,
        },
    )
    BoundValue = ReplaceValue(
        BossValue,
        definition=ReplaceValue(Definition, second_length=LengthValue),
        parameter_ids=(*BossValue.parameter_ids, DormantId),
    )
    return ReplaceValue(
        DocumentValue,
        parameters=(*DocumentValue.parameters, DormantValue),
        feature_timeline=tuple(
            BoundValue if StepValue is BossValue else StepValue
            for StepValue in DocumentValue.feature_timeline
        ),
    )
