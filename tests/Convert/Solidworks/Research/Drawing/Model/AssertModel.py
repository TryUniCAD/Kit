# model process proof must retain the actual complete graph and honest remaining factory boundaries
def AssertModel(Result: dict[str, object], MapValue: int) -> None:
    for FieldName in (
        "passed",
        "plain_sdk_model",
        "self_component_owner",
        "relation_runtime_owner",
        "active_sheet_identity",
        "manager_backlinks",
        "sdk_model_factory",
        "all_logical_streams_identical",
        "complete_sdk_read_write_identical",
        "research_ui_metadata_retained",
    ):
        assert Result[FieldName] is True
    for FieldName in (
        "research_parent_factory_retained",
        "complete_sdk_only_drawing_factory",
        "vendor_runtime_executed",
        "native_acceptance",
        "public_writer_enabled",
    ):
        assert Result[FieldName] is False
    assert Result["root_id"] == 0 and Result["root_next_id"] == 9
    assert Result["auxiliary_lists"] == 3 and Result["canonical_view_count"] == 10
    assert Result["shared_owner_guard_rejections"] == 3
    assert Result["ordered_child_ids"] == [3, -1, 2, 1, 8, -1, 4]
    assert Result["definition_map_next_index"] == MapValue
    assert (
        Result["runtime_input_file_access_attempts"]
        == Result["heldout_inputs_read"]
        == 0
    )
