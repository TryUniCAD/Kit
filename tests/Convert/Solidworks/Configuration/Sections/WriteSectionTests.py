from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# the complete shared emitter and reader processes must agree on section bytes and map identities
def TestCfgWrite() -> None:
    Probe = (
        FilePath(__file__).resolve().parents[5]
        / "re/tooling/sw2026/CheckCfgSectionWrite.py"
    )
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Probe), "measure"),
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stderr.decode()
    Proof = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Proof["runtime_external_accesses"] == 0
    assert Proof["guarded_fresh_processes"] == 2
    Single, Directory = CastValue(list[dict[str, object]], Proof["models"])
    assert (Single["bytes"], Directory["bytes"]) == (32, 44)
    assert Single["windows"] == [[18, 22], [26, 32]]
    assert Directory["windows"] == [[18, 22], [26, 44]]
    assert (Single["config_ref_slot"], Directory["config_ref_slot"]) == (3, 5)
    assert (Single["map_counter"], Directory["map_counter"]) == (4, 6)
    assert CastValue(dict[str, object], Single["missing_alias"])["outer_cursor"] == 22
    Ladder, Concave, Signed = CastValue(list[dict[str, object]], Proof["ghosts"])
    assert Ladder["native_interval"] == [3174, 3182]
    assert Concave["native_interval"] == [2227, 2235]
    assert (
        Ladder["signed_flags"],
        Concave["signed_flags"],
        Signed["signed_flags"],
    ) == (1, 0, -8)
    Refusals = CastValue(list[dict[str, object]], Proof["refusals"])
    assert len(Refusals) == 12
    assert any(
        ItemValue["case"] == "nested_part" and ItemValue["outer_bytes"] == 18
        for ItemValue in Refusals
    )
