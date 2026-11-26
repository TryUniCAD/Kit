from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# the constructor probe runs from a separate directory with only its declared case
KFreshHeadProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckFreshHeads.py"
)


# a fresh process proves header construction and decoding do not depend on prior document data
def RunFreshHead(CaseName: str, TmpPath: FilePath) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KFreshHeadProbe), CaseName),
        capture_output=True,
        encoding="utf-8",
        cwd=TmpPath,
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["case"] == CaseName
    assert ReportValue["external_accesses"] == 0
    assert list(TmpPath.iterdir()) == []
    return ReportValue
