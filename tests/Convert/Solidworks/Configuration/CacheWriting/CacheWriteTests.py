from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# fresh archive workers must preserve native framing and reject unowned cache state
def TestCacheWrite() -> None:
    Probe = (
        FilePath(__file__).resolve().parents[5]
        / "re/tooling/sw2026/CheckCfgCacheWrite.py"
    )
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Probe), "measure"),
        capture_output=True,
        check=False,
        timeout=90,
    )
    assert Outcome.returncode == 0, Outcome.stderr.decode("utf-8")
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Report["runtime_external_accesses"] == 0
    assert Report["guarded_fresh_processes"] == 3
    Ladder, Concave, Authored = CastValue(list[dict[str, object]], Report["cases"])
    assert (Ladder["case"], Concave["case"], Authored["case"]) == (
        "ladder",
        "concave",
        "authored",
    )
    LadderRows = CastValue(dict[str, dict[str, object]], Ladder["records"])
    ConcaveRows = CastValue(dict[str, dict[str, object]], Concave["records"])
    assert (LadderRows["mass"]["map_counter"], ConcaveRows["mass"]["map_counter"]) == (
        108,
        94,
    )
    assert all(
        RowValue["exact_byte_identity"] is True
        for RowsValue in (LadderRows, ConcaveRows)
        for RowValue in RowsValue.values()
    )
    ModelRows = CastValue(dict[str, dict[str, object]], Authored["records"])
    assert [ModelRows[KeyValue]["bytes"] for KeyValue in ("one_slot", "two_slots")] == [
        305,
        329,
    ]
    assert ModelRows["two_slots"]["sha256"] != ModelRows["changed_selector"]["sha256"]
    assert Authored["refusals"] == [
        "extra_slot",
        "inactive_selector",
        "missing_selector",
        "inactive_property",
        "absent_property",
        "missing_atom_rows",
        "unmodeled_atom",
        "missing_property_member",
        "unmodeled_vector",
        "populated_bounds",
        "missing_owner",
        "wrong_version",
        "unsupported_kind",
    ]
