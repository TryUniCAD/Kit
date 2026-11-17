from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarMate import PlanarMate
from interchange import (
    MateAlignment,
    MateConstraint,
    MateEntity,
    MateKind,
    ParameterValue,
    Provenance,
    ValueKind,
    frozen_mapping as FrozenMapping,
)


# complete typed mates supply the live driving length while retaining existing rule ids and ownership
def MakeMateRule(
    PlanValue: PlanarMate,
    NodeValue: ArchiveNode,
    LegacyValue: MateConstraint,
    Entities: tuple[MateEntity, ...],
    ProvenanceValue: Provenance,
) -> MateConstraint:
    LengthValue = PlanValue.DistanceValue
    return ReplaceValue(
        LegacyValue,
        name=PlanValue.NameValue,
        kind=MateKind(PlanValue.KindValue),
        entity_ids=tuple(Value.id for Value in Entities),
        value=(
            ParameterValue(LengthValue * 1000.0, ValueKind.LENGTH, "mm")
            if LengthValue is not None
            else None
        ),
        alignment=MateAlignment.ALIGNED,
        provenance=ProvenanceValue,
        attributes=FrozenMapping(
            {
                **LegacyValue.attributes,
                "native_value_m": LengthValue,
                "typed_archive_owner": {
                    "stream": "Contents/Config-0-MatesList",
                    "offset": NodeValue.StartOffset,
                    "end": NodeValue.EndOffset,
                    "map_index": NodeValue.IndexValue,
                    "native_feature_id": PlanValue.MateId,
                    "class_name": PlanValue.ClassName,
                    "archive_version": 19000,
                },
            }
        ),
    )
