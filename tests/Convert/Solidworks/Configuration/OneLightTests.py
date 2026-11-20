from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.ReadSceneCase import ReadSceneCase


# the original one direction save must supply its own scene and named light graph
def TestOneLight() -> None:
    ReportValue = ReadSceneCase("one")
    assert ReportValue["counter"] == [70, 79]
    assert ReportValue["directional_count"] == 1
    assert ReportValue["normalization_calls"] == 2
    assert ReportValue["scene_span"] == [20822, 21668]
    assert ReportValue["scene_sha256"] == (
        "a2c9d81bef7fdb60dc608d76339dbc5661b7b551af27a79d28c11f9b43dae321"
    )
    assert ReportValue["part_root_sha256"] == (
        "11bba7ab76912873a06da79bab0539045bcc9a1809541f4bbb69362f081e7036"
    )
    MembersValue = CastValue(list[dict[str, object]], ReportValue["members"])
    assert [ItemValue["slots"] for ItemValue in MembersValue] == [
        [70, 71, 72],
        [73, 74, 75],
        [76, 77, 78],
    ]
    assert [ItemValue["native_f08"] for ItemValue in MembersValue] == [6, 12, 13]
    assert [ItemValue["name"] for ItemValue in MembersValue] == [
        "Lights and Cameras",
        "Ambient",
        "Directional1",
    ]
    assert [ItemValue["record_bytes"] for ItemValue in MembersValue] == [846, 291, 343]
    assert MembersValue[2]["direction"] == [0.5417, 0.7071, -0.4545]
    assert all(ItemValue["normalization"] == [0, 0] for ItemValue in MembersValue[1:])
