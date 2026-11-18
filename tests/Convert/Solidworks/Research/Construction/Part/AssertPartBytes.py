from typing import cast as CastValue


# complete candidate proof must compare every native payload across independent typed preparation and fresh neutral mathematical construction
def AssertPartBytes(
    BuildValue: dict[str, object],
    Prepared: dict[str, object],
    Counterpart: dict[str, object],
) -> None:
    StreamsValue = CastValue(dict[str, dict[str, object]], BuildValue["streams"])
    ExpectedNames = {
        "Header2",
        "Contents/Config-0-ModelHeader",
        "Contents/Config-0",
        "Contents/CMgr",
        "Contents/CMgrHdr2",
        "Contents/Config-0-ResolvedFeatures",
        "Contents/Definition",
        "_MO_VERSION_19000/Biography",
        "_MO_VERSION_19000/History",
        "swXmlContents/KeyWords",
    }
    assert StreamsValue.keys() == ExpectedNames
    for ReportValue, FlagName in (
        (Prepared, "byte_identity"),
        (Counterpart, "same_as_independent_research"),
    ):
        ActualValue = CastValue(dict[str, dict[str, object]], ReportValue["streams"])
        assert ActualValue.keys() == ExpectedNames
        for NameValue, RowValue in ActualValue.items():
            assert RowValue[FlagName] is True
            assert RowValue["bytes"] == StreamsValue[NameValue]["bytes"]
            assert RowValue["sha256"] == StreamsValue[NameValue]["sha256"]
        assert ReportValue["config_map_counter"] == BuildValue["config_map_counter"]
        assert ReportValue["resolved_map_counter"] == BuildValue["resolved_map_counter"]
