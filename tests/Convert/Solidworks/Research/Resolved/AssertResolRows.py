from typing import cast as CastValue


# inherited aliases and complete schema evidence must remain distinct from full native model qualification
def AssertResolRows(Report: dict[str, object]) -> None:
    assert Report["passed"] is True and Report["public_full_linked_graph"] is False
    assert Report["writer_native_acceptance"] is False
    for RowValue in CastValue(list[dict[str, object]], Report["files"]):
        assert RowValue["byte_identity_passed"] is True
        assert RowValue["sha256"] == RowValue["output_sha256"]
        assert (
            RowValue["inherited_aliases_preserved"]
            is RowValue["manager_map_independent"]
            is True
        )
        assert CastValue(int, RowValue["inherited_entries"]) > 0
        assert all(
            CaseValue["rejected"]
            for CaseValue in CastValue(list[dict[str, object]], RowValue["malformed"])
        )
        assert {
            CaseValue["case"]
            for CaseValue in CastValue(
                list[dict[str, object]], RowValue["modeled_edits"]
            )
        } == {"modeled_feature_name"}
        for Direction in ("load", "store"):
            UsageValue = CastValue(dict[str, object], RowValue[Direction])
            assert UsageValue["completed"] is True and UsageValue["used_schemas"]
            assert (
                UsageValue["missing_schemas"] == UsageValue["provisional_schemas"] == []
            )
