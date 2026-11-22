from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# selected rollback identities must survive a fresh process and match the native owners
def TestHistMarks() -> None:
    ProbePath = (
        FilePath(__file__).resolve().parents[4]
        / "re/tooling/sw2026/CheckPartitionMarks.py"
    )
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(ProbePath), "measure"),
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stderr.decode()
    Evidence = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Evidence["guarded_fresh_processes"] == 5
    assert Evidence["runtime_external_accesses"] == 0
    Cases = CastValue(dict[str, dict[str, object]], Evidence["cases"])
    assert Cases["ladder"]["marks"] == [7, 3]
    assert Cases["ladder"]["transmit_slots"] == [177, 178]
    assert Cases["local"]["marks"] == [3, 2]
    assert Cases["initial"]["marks"] == [1, 0]
    assert all(
        Cases[NameValue]["validator_return"] is None
        for NameValue in ("ladder", "local", "initial")
    )
    Faults = CastValue(dict[str, object], Cases["ladder"]["refusals"])
    assert set(Faults) == {
        "detached_predecessor",
        "wrong_selected_mark",
        "deleted_owner_missing",
        "truncated_terminator",
        "appended_bytes",
    }
    assert all(
        "typed_refusal" in Cases[NameValue] for NameValue in ("legacy", "one_light")
    )
