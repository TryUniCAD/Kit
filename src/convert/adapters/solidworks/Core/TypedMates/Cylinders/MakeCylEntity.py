from collections.abc import Mapping

from convert.Geometry.Parasolid import NativeId
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylEndpoint import (
    CylEndpoint,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylWords import (
    ReadCylWords,
)
from interchange import (
    MateConstraint,
    MateEntity,
    MateEntityKind,
    Provenance,
    frozen_mapping as FrozenMapping,
)


# portable cylinder endpoints need the public face identity without losing persistent kernel and occurrence domains
def MakeCylEntity(
    Endpoint: CylEndpoint,
    ChildValue: CylChild,
    RuleValue: MateConstraint,
    OrderValue: int,
    ProvenanceValue: Provenance,
    LegacyMap: Mapping[str, MateEntity],
) -> MateEntity:
    EntityId = f"{RuleValue.id}:entity:{OrderValue}"
    LegacyValue = LegacyMap.get(EntityId)
    ItemValue = Endpoint.ItemValue
    return MateEntity(
        id=EntityId,
        owner_definition_id=RuleValue.owner_definition_id,
        instance_path=(f"sldasm:instance:{ItemValue.object_id}",),
        kind=MateEntityKind.CYLINDER,
        source_entity_id=NativeId("face", ChildValue.FaceValue.IndexValue + 1),
        radius=Endpoint.RadiusValue * 1000.0,
        provenance=ProvenanceValue,
        attributes=FrozenMapping(
            {
                **(LegacyValue.attributes if LegacyValue is not None else {}),
                "typed_archive_selection": True,
                "native_occurrence_feature_id": ItemValue.feature_id,
                "native_child_definition_id": ItemValue.definition_id,
                "native_child_configuration_id": ItemValue.configuration_id,
                "native_child_update_stamp": Endpoint.StampValue,
                "native_child_sha256": ChildValue.SourceHash,
                "native_face_node_id": ChildValue.FaceValue.Integer("node_id"),
                "native_face_transmit_index": ChildValue.FaceValue.IndexValue + 1,
                "native_body_atom_id": ChildValue.AtomValue,
                "native_surface_feature_id": FieldInt(
                    ChildValue.FeatureValue.FieldsValue, "f08"
                ),
                "native_surface_arc_permanent_marker": ChildValue.ArcMarker,
                "native_kernel_face_ids": ReadCylWords(
                    ChildValue.NodesValue, ChildValue.FaceValue
                ),
                "native_kernel_face_aux_ids": ReadCylWords(
                    ChildValue.NodesValue, ChildValue.FaceValue, 3
                ),
                "stored_origin_m": Endpoint.OriginValue,
                "stored_axis": Endpoint.AxisValue,
                "native_radius_m": Endpoint.RadiusValue,
            }
        ),
    )
