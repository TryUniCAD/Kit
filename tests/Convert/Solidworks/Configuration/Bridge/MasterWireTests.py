from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.Bridge.RunMasterCase import RunMasterCase


# independently framed counts distinguish retained width from active inherited rows
def TestMasterWire() -> None:
    Measured = RunMasterCase("circular")
    Authored = CastValue(dict[str, object], Measured["authored"])
    Positives = CastValue(list[dict[str, object]], Authored["positive"])
    assert [RowValue["selector"] for RowValue in Positives] == [-7, 41, -7]
    assert [RowValue["bytes"] for RowValue in Positives] == [201, 213, 205]
    NodesValue = [
        CastValue(dict[str, object], RowValue["node"]) for RowValue in Positives
    ]
    assert [NodeValue["inherited_count_width"] for NodeValue in NodesValue] == [2, 2, 6]
    assert NodesValue[2]["fields_sha256"] == (
        "84f4d717aa3bc1f0fb2e2ba3c9b2ca3efafc39ddd4a51b43606fc670af847cd8"
    )
    assert Authored["refusals"] == [
        "wrong_version",
        "detached_part",
        "trailing_absent",
        "missing_direct_owner",
        "wrong_tagged_frame",
        "borrowed_part_link",
        "nonempty_list",
        "negative_list",
        "nonempty_inherited_list",
        "nonzero_inherited_tail",
        "appended_present",
    ]
