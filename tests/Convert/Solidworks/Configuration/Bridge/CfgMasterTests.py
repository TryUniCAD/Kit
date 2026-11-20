from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.Bridge.RunMasterCase import RunMasterCase

# the saved controls qualify both selector outputs at their actual shared map counters
KMasterCases = (
    ("rectangle", [25099, 25103], 105, 0, None),
    ("circular", [25320, 25473], 119, 1, 1),
    ("circle-save", [24214, 24367], 118, 1, 0),
)


# native results must preserve the selector window and the distinct owned feature state
def TestMaster() -> None:
    for CaseName, Interval, CountValue, Selector, Variant in KMasterCases:
        Measured = RunMasterCase(CaseName)
        assert Measured["interval"] == Interval
        assert Measured["selector"] == Selector
        assert Measured["counter"] == [CountValue, CountValue]
        assert Measured["body_bytes"] == (149 if Selector else 0)
        if Variant is None:
            assert Measured["result"] is None
            continue
        NodeValue = CastValue(dict[str, object], Measured["result"])
        assert NodeValue["class"] == "moSheetMetalMaster_c"
        assert NodeValue["schema"] == 1
        assert NodeValue["index"] is None
        assert NodeValue["native_id"] == -1
        assert NodeValue["variant"] == Variant


# independent frames distinguish sign and body extent while invalid paths remain bounded
def TestMasterWire() -> None:
    Measured = RunMasterCase("circular")
    Authored = CastValue(dict[str, object], Measured["authored"])
    Positives = CastValue(list[dict[str, object]], Authored["positive"])
    assert [RowValue["selector"] for RowValue in Positives] == [-7, 41]
    assert [RowValue["bytes"] for RowValue in Positives] == [201, 213]
    assert Authored["refusals"] == [
        "wrong_version",
        "detached_part",
        "trailing_absent",
        "missing_direct_owner",
        "wrong_tagged_frame",
        "borrowed_part_link",
        "nonempty_list",
        "negative_list",
        "appended_present",
    ]
