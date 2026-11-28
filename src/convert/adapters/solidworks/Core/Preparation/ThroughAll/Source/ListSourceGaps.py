from interchange.document.Models.DocumentModel import CadDocument


# supported shape owners cannot certify source settings and history that have no qualified construction projection
def ListSourceGaps(DocumentValue: CadDocument) -> tuple[str, ...]:
    Result = [
        "source:header_author_biography_and_history_not_projected",
        "metadata/solidworks.typed_configuration_graph:source_style_units_and_scene_not_constructed",
        "metadata/solidworks.typed_configuration_manager:source_configuration_settings_not_constructed",
        "metadata/solidworks.typed_resolved_semantics/native_tree:owned_system_state_not_constructed",
        "metadata/solidworks.typed_resolved_semantics/native_tree:full_native_presentation_unqualified",
        "metadata:source_wrapper_payload_and_unclassified_metadata_observation_only",
        "feature_timeline:source_attributes_and_provenance_not_constructed",
        "selections:continuous_automatic_scope_not_encoded_or_qualified",
    ]
    Result.extend(
        "sketches/" + Value.id + "/attributes:native_sketch_state_not_constructed"
        for Value in DocumentValue.sketches
    )
    Result.extend(
        "bodies/" + Value.id + "/name:caption_authority_unqualified"
        for Value in DocumentValue.bodies
    )
    for FieldName in ("document_summary", "custom_properties"):
        if DocumentValue.metadata.get(FieldName):
            Result.append(
                "metadata/"
                + FieldName
                + ":source_text_not_constructed_by_owner_component"
            )
    Result.extend(
        "configurations/"
        + Value.id
        + "/attributes:source_text_not_constructed_by_owner_component"
        for Value in DocumentValue.configurations
        if Value.attributes.get("custom_properties")
    )
    return tuple(Result)
