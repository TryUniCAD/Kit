from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)
from interchange import (
    MateAlignment,
    MateConstraint,
    MateEntity,
    Provenance,
    frozen_mapping as FrozenMapping,
)


# concentric orientation and actual rotation lock must remain authored semantics rather than unknown legacy text
def MakeCylRule(
    NodeValue: ArchiveNode,
    LegacyValue: MateConstraint,
    Entities: tuple[MateEntity, ...],
    ProvenanceValue: Provenance,
) -> MateConstraint:
    FieldsValue = NodeValue.FieldsValue
    return ReplaceValue(
        LegacyValue,
        name=ReadNodeName(NodeValue),
        entity_ids=tuple(Value.id for Value in Entities),
        alignment=(
            MateAlignment.ALIGNED
            if FieldInt(FieldsValue, "f3b4") == 1
            else MateAlignment.ANTI_ALIGNED
        ),
        provenance=ProvenanceValue,
        attributes=FrozenMapping(
            {
                **LegacyValue.attributes,
                "rotation_locked": FieldInt(FieldsValue, "f4b8") == 1,
                "native_rotation_lock_code": FieldInt(FieldsValue, "f4b8"),
                "native_internal_alignment_code": FieldInt(FieldsValue, "f3b4"),
                "native_solved_state_code": FieldInt(FieldsValue, "f3b8"),
                "typed_archive_owner": {
                    "stream": "Contents/Config-0-MatesList",
                    "offset": NodeValue.StartOffset,
                    "end": NodeValue.EndOffset,
                    "map_index": NodeValue.IndexValue,
                    "native_feature_id": FieldInt(FieldsValue, "f08"),
                    "class_name": NodeValue.ClassValue.NameValue,
                    "archive_version": 19000,
                },
            }
        ),
    )
