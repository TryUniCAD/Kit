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
