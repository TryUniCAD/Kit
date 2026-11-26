from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# each disclosed suffix requires an isolated process with the real header and map
KMatProbe = FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckCfgMat.py"


# the queue needs the guarded archive result and its diagnostic output
def ReadMatCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KMatProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["runtime_external_accesses"] == 0
    assert ReportValue["inherited_slots"] == [1, 2, 3]
    return ReportValue
