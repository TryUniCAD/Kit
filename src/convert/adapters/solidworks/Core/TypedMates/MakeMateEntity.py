from collections.abc import Mapping

from convert.adapters.solidworks.Assembly.PlanarMates.PlanarEndpoint import (
    PlanarEndpoint,
)
from interchange import (
    MateConstraint,
    MateEntity,
    MateEntityKind,
    Provenance,
    frozen_mapping as FrozenMapping,
)


# typed occurrence and datum identities replace optional legacy selection text without changing neutral ids
def MakeMateEntity(
    Endpoint: PlanarEndpoint,
    RuleValue: MateConstraint,
    OrderValue: int,
    ProvenanceValue: Provenance,
    LegacyMap: Mapping[str, MateEntity],
    *,
    Deferred: bool = False,
) -> MateEntity:
    EntityId = f"{RuleValue.id}:entity:{OrderValue}"
    LegacyValue = LegacyMap.get(EntityId)
    return MateEntity(
        id=EntityId,
        owner_definition_id=RuleValue.owner_definition_id,
        instance_path=(f"sldasm:instance:{Endpoint.OccurrenceObjectId}",),
        kind=MateEntityKind.PLANE,
        source_entity_id=f"sldprt:plane:{Endpoint.DatumFeatureId}",
        provenance=ProvenanceValue,
        attributes=FrozenMapping(
            {
                **(LegacyValue.attributes if LegacyValue is not None else {}),
                "typed_archive_selection": True,
                "native_occurrence_feature_id": Endpoint.OccurrenceFeatureId,
                "native_child_definition_id": Endpoint.ChildDefinitionId,
                "native_child_configuration_id": Endpoint.ChildConfigId,
                "native_child_update_stamp": Endpoint.ChildUpdateStamp,
                "native_datum_feature_id": Endpoint.DatumFeatureId,
                **({} if Deferred else {"native_datum_name": Endpoint.DatumName}),
                "stored_origin_m": Endpoint.OriginValue,
                "stored_normal": Endpoint.NormalValue,
            }
        ),
    )
