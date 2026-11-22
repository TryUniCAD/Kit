from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# the bounded helper must run in a fresh guarded process for each document
KFinishProbe = (
    FilePath(__file__).resolve().parents[5] / "re/tooling/sw2026/CheckCfgFinish.py"
)


# process diagnostics must remain visible when a scoped archive replay fails
def RunFinishCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KFinishProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Result = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Result["case"] == CaseName
    assert Result["runtime_external_accesses"] == 0
    return Result
