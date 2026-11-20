from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# the actual member bytes must reach the native field dispatcher inside an isolated process
KActionProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckCfgOwners.py"
)


# queue runs must surface assertion failures from the guarded native reader process
def ReadOwnerCase(
    CaseName: str,
) -> tuple[dict[str, object], dict[str, object], list[str]]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KActionProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["runtime_external_accesses"] == 0
    BlockValue, ExplodedValue = CastValue(
        list[dict[str, object]], ReportValue["records"]
    )
    return BlockValue, ExplodedValue, CastValue(list[str], ReportValue["refusals"])


# the block record must keep its own map backlink and the exact native guid field
def TestBlockOwner() -> None:
    BlockValue, ExplodedValue, Refusals = ReadOwnerCase("ladder")
    assert BlockValue["field"] == "fe80"
    assert BlockValue["bytes"] == 199
    assert BlockValue["class_name"] == "moSketchBlockMgr_c"
    assert BlockValue["class_slot"] == 97
    assert BlockValue["object_slot"] == BlockValue["backlink_slot"] == 98
    assert BlockValue["counter"] == [97, 99]
    assert BlockValue["inherited_map_slots"] == [59, 60, 95, 96]
    assert BlockValue["branch_calls"] == 5
    assert BlockValue["virtual_calls"] == 4
    assert BlockValue["xml_layout"] is False
    assert BlockValue["guid_sha256"] == (
        "f58dbac47df9237a6204d9e6939e2a0c2943b34d1d6c0ff7f0142adcc5bd79dd"
    )
    CheckExplRecord(ExplodedValue)
    CheckRefusals(Refusals)


# the separate exploded view owner selects a concrete xml target without adding a payload
def CheckExplRecord(RecordValue: dict[str, object]) -> None:
    assert RecordValue["field"] == "f13f8"
    assert RecordValue["bytes"] == 195
    assert RecordValue["class_name"] == "moPrtExplViewManager_c"
    assert RecordValue["class_slot"] == 108
    assert RecordValue["object_slot"] == 109
    assert RecordValue["counter"] == [108, 110]
    assert RecordValue["inherited_map_slots"] == [59, 60, 95, 96, 97, 98]
    assert RecordValue["branch_calls"] == 6
    assert RecordValue["virtual_calls"] == 4
    assert RecordValue["xml_layout"] is True
    assert RecordValue["feature_index"] == 19
    assert RecordValue["word_map_count"] == RecordValue["resolved_items"] == 0


# actual framing and semantic refusals must both run after the positive native controls
def CheckRefusals(Refusals: list[str]) -> None:
    assert Refusals == [
        "truncated_guid",
        "trailing",
        "wrong_owner",
        "wrong_archive_version",
        "wrong_map_counter",
        "null_backlink",
        "inherited_backlink",
        "reused_root",
        "populated_name",
        "populated_map",
        "missing_virtual",
    ]


# the two optional fields of the concave control must preserve their native map handoffs
def TestNullOwners() -> None:
    BlockValue, ExplodedValue, Refusals = ReadOwnerCase("concave")
    assert [BlockValue["field"], ExplodedValue["field"]] == ["fe80", "f13f8"]
    assert BlockValue["counter"] == [90, 90]
    assert ExplodedValue["counter"] == [94, 94]
    for RecordValue in (BlockValue, ExplodedValue):
        assert RecordValue["bytes"] == 2
        assert RecordValue["class_slot"] is RecordValue["object_slot"] is None
        assert RecordValue["branch_calls"] == RecordValue["virtual_calls"] == 0
        assert RecordValue["inherited_map_slots"] == [52, 53]
    assert not Refusals
