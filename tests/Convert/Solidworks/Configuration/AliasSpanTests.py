from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.ReadSectionCase import ReadSectionCase

# the first section binds the alias before the second section consumes its own body
KLinkedWindows: list[dict[str, object]] = [
    {"body": [18, 22], "cursor": 22, "map_before": [1, 3], "map_after": [4, 4]},
    {"body": [26, 32], "cursor": 32, "map_before": [4, 4], "map_after": [4, 4]},
]

# an absent alias stops the later body just after its reference tag
KMissingWindows: list[dict[str, object]] = [
    {"body": [18, 22], "cursor": 22, "map_before": [1, 3], "map_after": [3, 3]},
    {"body": [26, 32], "cursor": 28, "map_before": [3, 3], "map_after": [3, 3]},
]


# sibling windows resolve the original header owner through the live map
def TestSiblingSpan() -> None:
    ReportValue = ReadSectionCase("siblings")
    assert ReportValue["case"] == "siblings"
    assert ReportValue["wire_bytes"] == ReportValue["outer_cursor"] == 32
    assert ReportValue["header_slot"] == 69 and ReportValue["config_slot"] == 3
    assert ReportValue["map_base"] == ReportValue["map_counter"] == 4
    assert ReportValue["windows"] == KLinkedWindows
    FaultValue = CastValue(dict[str, object], ReportValue["missing_alias"])
    assert FaultValue["diagnostic"] == "unresolved archive object reference 3"
    assert FaultValue["outer_cursor"] == 22
    assert FaultValue["windows"] == KMissingWindows
