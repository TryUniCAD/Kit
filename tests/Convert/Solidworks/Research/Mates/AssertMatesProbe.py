from typing import cast as CastValue


# exact aliases and malformed stream rejection matter beyond matching one stream length
def AssertMates(Report: dict[str, object]) -> None:
    assert Report["passed"] is Report["byte_identity"] is True
    assert (
        Report["typed_readback_identity"]
        is Report["resolved_objects_unchanged"]
        is True
    )
    assert Report["mate_count"] == 1
    assert Report["mate_classes"] == ["moMateDistanceDim_c"]
    assert Report["empty_stream_bytes"] == 6 and Report["empty_no_allocation"] is True
    assert Report["inherited_map_aliases"] == Report["write_inherited_map_aliases"]
    assert Report["inherited_map_aliases"] == Report["readback_inherited_map_aliases"]
    RowsValue = CastValue(list[dict[str, object]], Report["endpoint_aliases"])
    assert [RowValue["ordinal"] for RowValue in RowsValue] == [0, 1]
    assert len({RowValue["occurrence_slot"] for RowValue in RowsValue}) == 2
    assert len({RowValue["external_slot"] for RowValue in RowsValue}) == 2
    assert all(RowValue["component_owner_is_model"] for RowValue in RowsValue)
    assert all(RowValue["external_identity_preserved"] for RowValue in RowsValue)
    Failures = CastValue(list[dict[str, object]], Report["negatives"])
    assert len(Failures) == 14 and all(RowValue["rejected"] for RowValue in Failures)
    assert {RowValue["case"] for RowValue in Failures} >= {
        "counter_only_context",
        "missing_actual_external_alias",
        "unsupported_mate_schema",
        "unsupported_version",
        "nonplane_wrapper_reference",
    }
