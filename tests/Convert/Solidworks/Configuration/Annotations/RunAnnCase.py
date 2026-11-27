from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# real configuration sources need a fresh process before evaluating their annotation records
KAnnProbe = FilePath(__file__).resolve().parents[5] / "re/tooling/sw2026/CheckCfgAnn.py"


# queue failures need the exact archive diagnostics from the guarded annotation process
def RunAnnCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KAnnProbe), CaseName),
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
