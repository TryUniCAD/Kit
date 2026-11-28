from typing import cast as CastValue


# a complete source only blank file requires every sdk stream readback plus portable semantics and an honest unmeasured native boundary
def AssertPortable(Result: dict[str, object]) -> None:
    for FieldName in (
        "passed",
        "complete_sdk_only_blank_factory",
        "complete_sdk_read_write_identical",
        "neutral_drawing_semantics",
        "actual_self_file_identity",
    ):
        assert Result[FieldName] is True
    for FieldName in (
        "research_builder_modules_loaded",
        "vendor_runtime_executed",
        "native_acceptance",
    ):
        assert Result[FieldName] is False
    assert Result["public_write_refusals"] == {
        "inspection": True,
        "linked_layout": False,
    }
    assert (
        Result["runtime_input_file_access_attempts"]
        == Result["heldout_inputs_read"]
        == 0
    )
    assert Result["native_sheet_id"] == 4 and Result["definition_map_next_index"] == 131
    assert len(CastValue(dict[str, object], Result["streams"])) == 7
    assert Result["source_sheet_id"]
