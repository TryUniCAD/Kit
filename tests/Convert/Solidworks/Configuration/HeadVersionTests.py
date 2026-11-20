from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.RunHeadLink import RunHeadLink


# malformed streams must expose the version guard before either typed payload reader
def TestHeadVersion() -> None:
    ReportValue = RunHeadLink("version-order")
    Records = CastValue(list[dict[str, object]], ReportValue["stages"])
    Older, HeaderFault, ConfigFault = Records
    assert [Record["physical_format"] for Record in Records] == [4, 4, 4]
    assert [Record["logical_version"] for Record in Records] == [18900, 19000, 19000]
    assert [Record["stage"] for Record in Records] == [
        "wrong_version",
        "current_bad_header",
        "current_bad_config",
    ]
    assert Older["diagnostic"] == (
        "SOLIDWORKS configuration start requires format 4 at version 19000"
    )
    assert HeaderFault["diagnostic"] == "truncated SOLIDWORKS archive field at 2"
    assert ConfigFault["diagnostic"] == "archive tag has no complete unsigned dword"
    OlderLanes = CastValue(dict[str, str], Older["required_lane_sha256"])
    ConfigLanes = CastValue(dict[str, str], ConfigFault["required_lane_sha256"])
    assert OlderLanes == HeaderFault["required_lane_sha256"]
    assert OlderLanes["Contents/Config-0"] == ConfigLanes["Contents/Config-0"]
    assert (
        OlderLanes["Contents/Config-0-ModelHeader"]
        != ConfigLanes["Contents/Config-0-ModelHeader"]
    )
