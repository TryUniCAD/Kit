from typing import cast as CastValue


# roundtrip evidence must retain exact alias counters and independent manager context on both directions
def AssertCfgReport(Report: dict[str, object]) -> None:
    assert Report["passed"] is True and Report["public_full_linked_graph"] is False
    for RowValue in CastValue(list[dict[str, object]], Report["files"]):
        assert RowValue["byte_identity_passed"] is True
        assert RowValue["sha256"] == RowValue["output_sha256"]
        assert (
            RowValue["manager_map_independent"] is True
            and RowValue["manager_map_base"] == 1
        )
        ContextValue = CastValue(dict[str, int], RowValue["resolved_context"])
        assert (
            ContextValue["model_compressed_stream"] == 1 and "cmgr_f658" in ContextValue
        )
        for AliasValue in CastValue(
            list[dict[str, object]], RowValue["header_direct_aliases"]
        ):
            assert (
                AliasValue["index"] == AliasValue["stored_index"]
                and AliasValue["same_header_object"] is True
            )
        for Direction in ("load", "store"):
            UsageValue = CastValue(dict[str, object], RowValue[Direction])
            assert UsageValue["completed"] is True and UsageValue["used_schemas"]
            assert (
                UsageValue["missing_schemas"] == UsageValue["provisional_schemas"] == []
            )
        assert all(
            RowValue["rejected"]
            for RowValue in CastValue(list[dict[str, object]], RowValue["malformed"])
        )
        assert {
            RowValue["case"]
            for RowValue in CastValue(
                list[dict[str, object]], RowValue["modeled_edits"]
            )
        } == {"modeled_name", "modeled_array_count"}
