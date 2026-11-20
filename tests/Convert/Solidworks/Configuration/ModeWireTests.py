from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.RunModeCase import RunModeCase

# authored modes must still refuse unsupported field calibration and malformed records
KModeRefusals = [
    "branch",
    "fixed_negative",
    "fixed_limit",
    "fixed_truncated",
    "normalization",
    "signed_width",
    "direct_owner",
    "component_owner",
]


# predicate choices and normalized wire values must agree at the full body boundary
def TestFieldModes() -> None:
    ReportValue = RunModeCase("authored")
    Records = CastValue(list[dict[str, object]], ReportValue["records"])
    Below, Equal, Above = [
        CastValue(dict[str, object], Record["fields"]) for Record in Records
    ]
    assert [Record["bytes"] for Record in Records] == [72, 72, 72]
    assert [Record["conditions"] for Record in Records] == [0, 0x20, 0xA0]
    assert Below["different"] == Equal["equal"] == Above["different"] == 31
    assert Below["not_above"] == Equal["not_above"] == Above["above"] == 47
    assert Below["clear"] == Equal["clear"] == Above["masked"] == 59
    assert [
        Below["threshold#wire"],
        Equal["threshold#wire"],
        Above["threshold#wire"],
    ] == [
        -4,
        10,
        15,
    ]
    assert [Below["threshold"], Equal["threshold"], Above["threshold"]] == [10, 10, 15]
    assert Below["identity"] == Below["identity#wire"] == -78
    assert Below["scene"] == Equal["scene"] == Above["scene"] == 0
    assert Below["atom"] == Equal["atom"] == 0
    assert Above["atom"] == Above["atom#wire"] == 0xF00000C1
    for Fields in (Below, Equal, Above):
        assert Fields["fixed"] == [{"value": Index * Index - 9} for Index in range(10)]
        assert Fields["empty"] == []
    assert ReportValue["refusals"] == KModeRefusals
