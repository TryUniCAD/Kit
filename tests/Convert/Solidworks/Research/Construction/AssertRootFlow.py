from typing import cast as CastValue


# root proof needs actual identity cycles constructor allocations and complete separate sdk byte comparisons
def AssertRootFlow(
    BuildValue: dict[str, object],
    Prepared: dict[str, object],
    RootId: int,
    NextValue: int,
) -> int:
    assert BuildValue["root_id"] == RootId and BuildValue["next_id"] == NextValue
    assert (
        BuildValue["plain_archive_node"]
        is BuildValue["self_component_owner"]
        is BuildValue["relation_runtime_owner"]
        is True
    )
    assert BuildValue["fresh_auxiliary_lists"] == Prepared["active_fresh_lists"] == 3
    assert BuildValue["view_count"] == Prepared["ordered_views"] == 10
    assert (
        Prepared["self_component_cycle"]
        is Prepared["relation_runtime_owner_absent"]
        is Prepared["independent_units"]
        is True
    )
    assert BuildValue["config_map_counter"] == Prepared["config_map_counter"]
    Failures = CastValue(list[dict[str, object]], BuildValue["malformed"])
    assert len(Failures) == 10 and all(RowValue["rejected"] for RowValue in Failures)
    Original = CastValue(dict[str, dict[str, object]], BuildValue["streams"])
    StreamsValue = CastValue(dict[str, dict[str, object]], Prepared["streams"])
    assert (
        Original.keys()
        == StreamsValue.keys()
        == {"Contents/Config-0", "Contents/Config-0-ModelHeader"}
    )
    for StreamName, RowValue in StreamsValue.items():
        assert RowValue["byte_identity"] is True
        assert (
            RowValue["bytes"] == Original[StreamName]["bytes"]
            and RowValue["sha256"] == Original[StreamName]["sha256"]
        )
    for Report in (BuildValue, Prepared):
        UsageValue = CastValue(dict[str, object], Report["config_usage"])
        assert (
            UsageValue["completed"] is True
            and not UsageValue["missing_schemas"]
            and not UsageValue["provisional_schemas"]
        )
    return CastValue(int, StreamsValue["Contents/Config-0"]["bytes"])
