from typing import cast as CastValue


# independent preparation must reconstruct the same typed topology aliases and complete linked stream maps
def AssertPolyPrep(
    Report: dict[str, object], BuildValue: dict[str, object], CountValue: int
) -> None:
    assert Report["artifact_sha256"] == BuildValue["sha256"]
    assert Report["profile_sketch_alias"] is Report["model_owner_alias"] is True
    assert Report["runtime_backlink_not_serialized"] is True
    assert Report["extrusion_dependency_alias"] is Report["linked_map_aliases"] is True
    assert Report["config_map_counter"] == BuildValue["config_map_counter"]
    assert Report["resolved_map_counter"] == BuildValue["resolved_map_counter"]
    GeometryValue = CastValue(dict[str, object], Report["geometry"])
    assert GeometryValue["point_count"] == GeometryValue["line_count"] == CountValue
    assert GeometryValue["distinct_endpoint_handles"] == 2 * CountValue
    assert GeometryValue["index_encodings"] == {
        "compact_handles": 2 * CountValue,
        "extended_handles": 0,
        "compact_endpoints": 2 * CountValue,
        "extended_endpoints": 0,
    }
    assert all(
        GeometryValue[FieldName] is True
        for FieldName in (
            "ordered_endpoints",
            "positions",
            "creation_counters",
            "permanent_markers",
            "constructor_solver_state",
        )
    )
    StreamsValue = CastValue(dict[str, dict[str, object]], Report["streams"])
    OriginalValues = CastValue(dict[str, dict[str, object]], BuildValue["streams"])
    assert StreamsValue.keys() == OriginalValues.keys()
    for StreamName, RowValue in StreamsValue.items():
        assert RowValue["byte_identity"] is True
        assert RowValue["bytes"] == OriginalValues[StreamName]["bytes"]
        assert RowValue["sha256"] == OriginalValues[StreamName]["sha256"]
    UsageValue = CastValue(dict[str, object], Report["resolved_usage"])
    assert (
        UsageValue["completed"] is True
        and not UsageValue["missing_schemas"]
        and not UsageValue["provisional_schemas"]
    )
