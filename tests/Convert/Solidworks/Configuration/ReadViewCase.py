from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# each file requires a fresh guarded process that consumes its bounded native records
KViewProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckCfgViews.py"
)


# diagnostics and runtime access evidence belong to the shared process boundary
def ReadViewCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KViewProbe), CaseName),
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
