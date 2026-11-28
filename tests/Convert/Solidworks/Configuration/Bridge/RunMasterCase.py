from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# the queue must observe selector handling in a process with the runtime guard active
KMasterProbe = (
    FilePath(__file__).resolve().parents[5] / "re/tooling/sw2026/CheckCfgMaster.py"
)


# each complete body check must report an independent process result
def RunMasterCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KMasterProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Record = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Record["runtime_external_accesses"] == 0
    assert Record["base"] == 4
    return Record
