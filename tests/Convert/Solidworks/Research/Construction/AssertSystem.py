from typing import cast as CastValue


# system proof needs actual cross stream ownership independent identifiers complete grammar and complete byte comparisons rather than counts alone
def AssertSystem(
    BuildValue: dict[str, object], Prepared: dict[str, object], ConfigCount: int
) -> int:
    assert (
        BuildValue["configuration_count"]
        == Prepared["configuration_count"]
        == ConfigCount
    )
    assert BuildValue["feature_count"] == Prepared["feature_count"] == 17
    assert (
        BuildValue["global_allocations"] == 18
        and BuildValue["runtime_cache_count"] == 9
    )
    assert BuildValue["research_imports"] == 0
    assert all(
        BuildValue[NameValue] is True
        for NameValue in (
            "manager_local_namespace",
            "environment_alias",
            "exclusive_origin_component",
            "origin_fixed_relation",
            "pending_origin_update",
        )
    )
    assert all(
        Prepared[NameValue] is True
        for NameValue in (
            "environment_alias",
            "independent_manager_namespace",
            "actual_map_prefix_aliases",
            "origin_component_owner_alias",
            "compact_origin_index",
        )
    )
    assert Prepared["origin_point_count"] == Prepared["origin_fixed_relations"] == 1
    assert BuildValue["config_map_counter"] == Prepared["config_map_counter"]
    assert BuildValue["resolved_map_counter"] == Prepared["resolved_map_counter"]
    Failures = CastValue(list[dict[str, object]], BuildValue["malformed"])
    assert len(Failures) == 14 and all(RowValue["rejected"] for RowValue in Failures)
    Original = CastValue(dict[str, dict[str, object]], BuildValue["streams"])
    StreamsValue = CastValue(dict[str, dict[str, object]], Prepared["streams"])
    assert (
        Original.keys()
        == StreamsValue.keys()
        == {
            "Header2",
            "Contents/Config-0-ModelHeader",
            "Contents/Config-0",
            "Contents/CMgr",
            "Contents/Config-0-ResolvedFeatures",
        }
    )
    for StreamName, RowValue in StreamsValue.items():
        assert RowValue["byte_identity"] is True
        assert (
            RowValue["bytes"] == Original[StreamName]["bytes"]
            and RowValue["sha256"] == Original[StreamName]["sha256"]
        )
    for ReportValue in (BuildValue, Prepared):
        UsageValue = CastValue(dict[str, dict[str, object]], ReportValue["usage"])
        assert all(
            RowValue["completed"] is True
            and not RowValue["missing_schemas"]
            and not RowValue["provisional_schemas"]
            for RowValue in UsageValue.values()
        )
    return CastValue(int, StreamsValue["Contents/CMgr"]["bytes"])
