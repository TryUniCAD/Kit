from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.Bridge.RunMasterCase import RunMasterCase

# native controls pin complete field digests along with their selector windows
KMasterCases = (
    ("rectangle", [25099, 25103], 0, None, None),
    (
        "circular",
        [25320, 25473],
        1,
        1,
        "dadef17e06869eaf27508a7e37d04ea55662aa004fcfcdb124f8a31a73827a19",
    ),
    (
        "circle-save",
        [24214, 24367],
        1,
        0,
        "2f3c3bdd57b2042697c543f2440628a4808fc147540e340385af918552c200e9",
    ),
)


# the bounded queue process uses the physical part start and checks every decoded field
def TestMaster() -> None:
    for CaseName, Interval, Selector, Variant, FieldDigest in KMasterCases:
        Measured = RunMasterCase(CaseName)
        assert Measured["interval"] == Interval
        assert Measured["selector"] == Selector
        assert Measured["prefix_counter"] == 4
        assert Measured["prefix_slots"] == [1, 2, 3]
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
        assert NodeValue["inherited_count_width"] == 2
        assert NodeValue["fields_sha256"] == FieldDigest
