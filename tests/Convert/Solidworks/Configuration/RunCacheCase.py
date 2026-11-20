from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# physical cache intervals must reach the production archive decoder in a fresh process
KCacheProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckCfgCaches.py"
)


# both cache paths share the process guard and make a failed decoder check visible to the queue
def RunCacheCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KCacheProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["case"] == CaseName
    assert ReportValue["runtime_external_accesses"] == 0
    return ReportValue
