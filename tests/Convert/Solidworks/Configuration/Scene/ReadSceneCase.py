from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# each disclosed scene needs a fresh guarded process with its actual native parent
KSceneProbe = (
    FilePath(__file__).resolve().parents[5] / "re/tooling/sw2026/CheckCfgLights.py"
)


# the merge queue needs the isolated process outcome and its precise reader diagnostics
def ReadSceneCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KSceneProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["owner"] == "moPart_c.f1e0"
    assert ReportValue["runtime_external_accesses"] == 0
    assert ReportValue["inherited_slots"] == [4, 5]
    return ReportValue
