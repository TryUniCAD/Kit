from typing import cast as CastValue


# the bridge must preserve exact candidate bytes final identity and public ownership while rejecting an unnamed stream
def AssertBridge(ReportValue: dict[str, object]) -> int:
    for NameValue in (
        "exact_direct_candidate",
        "exact_named_configuration",
        "exact_configuration_id",
        "derived_neutral_units_and_support",
        "staging_path_not_encoded",
        "caller_destinations_unchanged",
        "public_save_rejected",
    ):
        assert ReportValue[NameValue] is True
    assert ReportValue["public_writer_available"] is True
    StreamsValue = CastValue(dict[str, object], ReportValue["streams"])
    assert len(StreamsValue) == 10
    PublicValue = CastValue(dict[str, object], ReportValue["public_read"])
    assert PublicValue["boss_name"] == "Boss-Extrude1"
    assert PublicValue["profile_name"] == "Sketch1"
    assert PublicValue["entity_count"] == 4
    assert PublicValue["driving_name"] == "D1"
    assert PublicValue["driving_owner"] is True
    Failures = CastValue(list[dict[str, object]], ReportValue["malformed"])
    assert len(Failures) == 21 and all(RowValue["rejected"] for RowValue in Failures)
    return CastValue(int, ReportValue["bytes"])
