from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.ReadSceneCase import ReadSceneCase


# the original two direction save must reuse its class while preserving distinct named owners
def TestTwoLights() -> None:
    ReportValue = ReadSceneCase("two")
    assert ReportValue["counter"] == [70, 81]
    assert ReportValue["directional_count"] == 2
    assert ReportValue["normalization_calls"] == 3
    assert ReportValue["scene_span"] == [20822, 21989]
    assert ReportValue["scene_sha256"] == (
        "f1d3f794a256035d858ac30fd574b775a793d0e9a042b769320fe6d330f6cc50"
    )
    MembersValue = CastValue(list[dict[str, object]], ReportValue["members"])
    assert [ItemValue["slots"] for ItemValue in MembersValue] == [
        [70, 71, 72],
        [73, 74, 75],
        [76, 77, 78],
        [76, 79, 80],
    ]
    assert [ItemValue["native_f08"] for ItemValue in MembersValue] == [6, 12, 13, 14]
    assert [ItemValue["class"] for ItemValue in MembersValue[2:]] == [
        "moDirectionLight_c",
        "moDirectionLight_c",
    ]
    assert [ItemValue["name"] for ItemValue in MembersValue[2:]] == [
        "Directional1",
        "Directional2",
    ]
    assert [ItemValue["direction"] for ItemValue in MembersValue[2:]] == [
        [0.5417, 0.7071, -0.4545],
        [-0.3971, 0.342, 0.8517],
    ]
    assert [ItemValue["record_bytes"] for ItemValue in MembersValue] == [
        1167,
        291,
        343,
        321,
    ]
    assert all(ItemValue["normalization"] == [0, 0] for ItemValue in MembersValue[1:])
