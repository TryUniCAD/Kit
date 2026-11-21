from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Mates.Distance.AssertDistWire import (
    AssertDistWire,
)


# exact bundle parity must retain a real local driving parameter and independent dimension allocation before mate publication
def AssertDistGraph(
    CurrentValue: dict[str, object],
    ReferenceValue: dict[str, object],
    LengthValue: float,
) -> None:
    assert CurrentValue["passed"] is ReferenceValue["passed"] is True
    for FieldName in ("assembly", "child", "mate_stream", "readback"):
        assert CurrentValue[FieldName] == ReferenceValue[FieldName], FieldName
    assert CurrentValue["runtime_file_read_attempts"] == 0
    assert CurrentValue["native_processes_started"] == 0
    assert CurrentValue["public_writer_enabled"] is False
    AssertDistWire(CastValue(dict[str, object], CurrentValue["mate_stream"]))
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
    DrivingValue = CastValue(dict[str, object], Constructor["driving_distance"])
    assert DrivingValue["value_metres"] == LengthValue
    assert DrivingValue["parameter_name"] == "D1"
    assert DrivingValue["parameter_id"] == -1
    assert DrivingValue["retaining_handle_count"] == 1
    assert DrivingValue["text_kind"] == 18
    assert DrivingValue["actual_feature_owners"] is True
    assert DrivingValue["actual_local_dimension"] is True
    assert DrivingValue["actual_retaining_handle"] is True
    assert CastValue(int, DrivingValue["dimension_id"]) < CastValue(
        int, DrivingValue["mate_id"]
    )
