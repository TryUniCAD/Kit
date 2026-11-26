from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# queue runs exercise an independent process with the archive guard active
KEmissionProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckAtomEmission.py"
)


# the result must include complete guarded verification before field assertions
def RunAtomEmission(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KEmissionProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["runtime_external_accesses"] == 0
    assert ReportValue["full_native_writer_qualified"] is False
    return ReportValue
