from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# each physical native thread and mark record must pass through a fresh archive process
KThreadProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckCfgThread.py"
)


# merge queue failures need the process diagnostics and the complete guarded result
def ReadThreadCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KThreadProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["runtime_external_accesses"] == 0
    return ReportValue


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
    AssertRefusals(ReportValue["refusals"])


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
