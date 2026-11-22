from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# physical configuration verification needs a fresh isolated sdk process
KConfigProbe = (
    FilePath(__file__).resolve().parents[5] / "re/tooling/sw2026/CheckOrdinaryCfg.py"
)


# the same guarded decoder must consume both real sections before reemission
def RunPartConfig(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KConfigProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Result = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Result["case"] == CaseName and Result["runtime_external_accesses"] == 0
    return Result
