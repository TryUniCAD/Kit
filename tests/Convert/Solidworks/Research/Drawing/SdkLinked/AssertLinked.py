from typing import cast as CastValue


# complete offline linked evidence must retain real generated ownership all stream readback and its unqualified native boundary
def AssertLinked(Result: dict[str, object], Counterpart: dict[str, object]) -> None:
    for FieldName in (
        "passed",
        "complete_sdk_only_linked_factory",
        "complete_sdk_read_write_identical",
        "neutral_drawing_semantics",
        "actual_generated_child_identity",
        "child_graph_reemission_unchanged",
    ):
        assert Result[FieldName] is True
    for FieldName in (
        "research_builder_modules_loaded",
        "vendor_runtime_executed",
        "native_acceptance",
        "public_writer_enabled",
    ):
        assert Result[FieldName] is False
    assert (
        Result["runtime_input_file_access_attempts"]
        == Result["heldout_inputs_read"]
        == 0
    )
    assert Result["native_sheet_id"] == 4 and Result["native_view_id"] == 11
    assert Result["model_next_id"] == 16 and Result["definition_map_next_index"] == 172
    assert len(CastValue(dict[str, object], Result["streams"])) == 7
    for FieldName in (
        "passed",
        "all_logical_streams_identical",
        "container_identical",
        "independent_corner_projection",
        "independent_canonical_frame",
    ):
        assert Counterpart[FieldName] is True
    assert (
        Counterpart["corner_count"] == 8
        and Counterpart["runtime_input_file_access_attempts"] == 0
    )
    assert Counterpart["artifact_sha256"] == Result["artifact_sha256"]
    assert Counterpart["streams"] == Result["streams"]
