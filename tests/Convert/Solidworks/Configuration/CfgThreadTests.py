from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.ReadThreadCase import ReadThreadCase


# the two physical marks use the live counter but retain independent kernel identifiers
def AssertMarkSpec(
    MarkValue: dict[str, object], ClassSlot: int, KernelMark: int
) -> None:
    assert MarkValue["field"] == "fe38"
    assert MarkValue["bytes"] == 25
    assert MarkValue["class"] == ["moPMarkRecord_c", 1]
    assert MarkValue["class_slot"] == ClassSlot
    assert MarkValue["object_slot"] == ClassSlot + 1
    assert MarkValue["counter"] == [ClassSlot, ClassSlot + 2]
    assert MarkValue["mark_id"] == KernelMark


# the ladder record and authored class references distinguish stored words from runtime state
def TestThreadOwner() -> None:
    ReportValue = ReadThreadCase("ladder")
    MarkValue, ThreadVal = CastValue(list[dict[str, object]], ReportValue["members"])
    AssertMarkSpec(MarkValue, 103, 3)
    assert MarkValue["inherited"] == [59, 60, 95, 96, 97, 98]
    assert ThreadVal["class"] == ["moCThreadRefMgr_c", 1]
    assert ThreadVal["field"] == "f12d0"
    assert ThreadVal["bytes"] == 31
    assert ThreadVal["counter"] == [106, 108]
    assert ThreadVal["class_slot"] == 106
    assert ThreadVal["object_slot"] == 107
    assert ThreadVal["inherited"] == [59, 60, 95, 96, 97, 98, 103, 104]
    assert ThreadVal["boolean_calls"] == 1
    assert ThreadVal["raw_word"] == ThreadVal["runtime_boolean"] == 0
    assert ReportValue["final_counter"] == 110
    assert ReportValue["final_slots"] == [
        59,
        60,
        95,
        96,
        97,
        98,
        103,
        104,
        106,
        107,
        108,
        109,
    ]
    assert ReportValue["authored_boolean_pairs"] == [
        [-2147483648, 1],
        [0, 0],
        [7, 1],
        [2147483647, 1],
    ]
    AssertAuthMark(ReportValue["authored_mark"])
    AssertRefusals(ReportValue["refusals"])


# the signed partition word and the inherited and new slots have distinct owners
def AssertAuthMark(MarkValue: object) -> None:
    assert MarkValue == {
        "bytes": 6,
        "class_slot": 103,
        "source_slot": 104,
        "object_slot": 105,
        "counter": [105, 106],
        "mark_id": -17,
    }


# every malformed or unqualified lane needs its own proven refusal
def AssertRefusals(Refusals: object) -> None:
    assert Refusals == [
        "truncated_mark",
        "null_mark",
        "truncated_boolean",
        "trailing",
        "wrong_archive_version",
        "wrong_role",
        "wrong_schema",
        "reused_thread",
        "missing_class",
        "negative_map_count",
        "populated_holder",
    ]


# a missing thread owner must preserve its mark map and never consume a boolean word
def TestNullThread() -> None:
    ReportValue = ReadThreadCase("concave")
    MarkValue, ThreadVal = CastValue(list[dict[str, object]], ReportValue["members"])
    AssertMarkSpec(MarkValue, 91, 2)
    assert MarkValue["inherited"] == [52, 53]
    assert ThreadVal == {
        "field": "f12d0",
        "bytes": 2,
        "counter": [94, 94],
        "class": None,
        "class_slot": None,
        "object_slot": None,
        "inherited": [52, 53, 91, 92],
        "boolean_calls": 0,
    }
    assert ReportValue["final_counter"] == 94
    assert ReportValue["final_slots"] == [52, 53, 91, 92]
    assert ReportValue["authored_boolean_pairs"] == ReportValue["refusals"] == []
    assert ReportValue["authored_mark"] is None
