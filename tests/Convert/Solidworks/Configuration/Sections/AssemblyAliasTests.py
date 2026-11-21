from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# a fresh assembly archive writer and reader must resolve the same ordered header objects
def TestAsmDirect() -> None:
    ProofPath = (
        FilePath(__file__).resolve().parents[5] / "re/tooling/sw2026/CheckAsmDirect.py"
    )
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(ProofPath), "measure"),
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stderr.decode()
    Proof = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Proof["runtime_external_accesses"] == 0 and Proof["guarded_processes"] == 2
    Models = CastValue(dict[str, dict[str, object]], Proof["authored"])
    First, Second = Models["one"], Models["two"]
    assert (First["bytes"], Second["bytes"]) == (38, 40)
    assert (First["sections"], Second["sections"]) == (
        [[22, 30], [34, 38]],
        [[22, 30], [34, 40]],
    )
    assert (First["map_base"], First["map_counter"], First["references"]) == (
        5,
        5,
        [4, 3],
    )
    assert (Second["map_base"], Second["map_counter"], Second["references"]) == (
        6,
        6,
        [5, 4, 3],
    )
    Refusals = CastValue(dict[str, str], Proof["refusals"])
    assert set(Refusals) == {
        "wrong_version",
        "nested",
        "detached",
        "duplicate_alias",
        "already_mapped_alias",
        "absent_alias",
    }
