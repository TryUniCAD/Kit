from typing import cast as CastValue


# whole generated containers must retain source independent semantics and exact linked stream bytes through the sdk constructor
def AssertSdkMate(
    CurrentValue: dict[str, object], ReferenceValue: dict[str, object]
) -> None:
    assert CurrentValue["passed"] is ReferenceValue["passed"] is True
    for FieldName in ("assembly", "child", "mate_stream", "readback"):
        assert CurrentValue[FieldName] == ReferenceValue[FieldName], FieldName
    assert CurrentValue["runtime_file_read_attempts"] == 0
    assert CurrentValue["native_processes_started"] == 0
    assert CurrentValue["public_writer_enabled"] is False
    assert CurrentValue["native_acceptance"] is False
    Constructor = CastValue(dict[str, object], CurrentValue["constructor"])
    assert all(
        Constructor[FieldName] is True
        for FieldName in (
            "independent_transform_caches",
            "distinct_resolved_wrappers",
            "distinct_detached_wrappers",
            "exclusive_detached_components",
            "parent_owner_identity",
            "actual_occurrence_backlinks",
        )
    )
    assert Constructor["unregistered_detached_planes"] == [-1, -1]
    MateStream = CastValue(dict[str, object], CurrentValue["mate_stream"])
    assert MateStream["map_terminal"] == Constructor["map_terminal"]
    Coverage = CastValue(dict[str, object], MateStream["read_coverage"])
    assert Coverage["completed"] is True
    for FieldName in ("missing_schemas", "provisional_schemas", "native_byte_fields"):
        assert not Coverage[FieldName]
