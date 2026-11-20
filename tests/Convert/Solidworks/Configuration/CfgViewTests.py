from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.ReadViewCase import ReadViewCase

# the source groups use these separate cases to exercise both compact transform widths
KViewNames = [
    "*Normal To",
    "*Front",
    "*Back",
    "*Left",
    "*Right",
    "*Top",
    "*Bottom",
    "*Isometric",
    "*Trimetric",
    "*Dimetric",
]


# wire groups must retain distinct objects under the one actual serialized class
def AssertViewRows(
    ReportValue: dict[str, object], ClassSlot: int, StartValue: int, EndValue: int
) -> None:
    ViewRows = CastValue(list[dict[str, object]], ReportValue["views"])
    assert ReportValue["counter"] == [ClassSlot, ClassSlot + 11]
    assert [ViewValue["slot"] for ViewValue in ViewRows] == list(
        range(ClassSlot + 1, ClassSlot + 11)
    )
    assert [ViewValue["name"] for ViewValue in ViewRows] == KViewNames
    assert all(
        ViewValue["class_slot"] == ClassSlot and ViewValue["context_calls"] == 4
        for ViewValue in ViewRows
    )
    Intervals = [CastValue(list[int], ViewValue["interval"]) for ViewValue in ViewRows]
    assert Intervals[0][0] == StartValue and Intervals[-1][1] == EndValue
    assert all(
        PriorValue[1] == NextValue[0]
        for PriorValue, NextValue in zip(Intervals[:-1], Intervals[1:])
    )
    for Index, ViewValue in enumerate(ViewRows):
        Matrix = int(Index >= 2)
        assert ViewValue["transforms"] == [[34 + Matrix * 72, Matrix, 0], [34, 0, 0]]


# the active condition branch must preserve other flags across both bounded list windows
def AssertViewState(ReportValue: object) -> None:
    State = CastValue(dict[str, object], ReportValue)
    assert State["slot"] == 95
    assert State["events"] == [
        ["conditions", 169, 4096, 4608],
        ["ctx87c", 169, 9, 1],
        ["ctx87c", 177, 1, 0],
        ["ctx87c", 177, 0, 1],
        ["ctx87c", 193, 1, 0],
        ["conditions", 193, 4608, 4096],
    ]
    assert State["flags"] == {"conditions": 4096, "ctx3d0": 1, "ctx87c": 0}


# unsupported presentation branches must fail while the exact source role stays usable
def TestLadderViews() -> None:
    ReportValue = ReadViewCase("ladder")
    AssertViewRows(ReportValue, 84, 22240, 24252)
    assert ReportValue["inherited"] == [59, 60]
    AssertViewState(ReportValue["authored"])
    assert ReportValue["refusals"] == [
        "truncated",
        "trailing",
        "null",
        "borrowed",
        "missing_class",
        "wrong_version",
        "wrong_role",
        "populated_links",
        "populated_first_list",
        "populated_second_list",
        "selected_transform",
        "unqualified_selector",
    ]


# the imported control supplies independent map positions for the same native view owner
def TestConcaveView() -> None:
    ReportValue = ReadViewCase("concave")
    AssertViewRows(ReportValue, 79, 20463, 22475)
    assert ReportValue["inherited"] == [52, 53]
