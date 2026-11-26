from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# queue coverage uses the same isolated worker as the disclosed history receipts
KHistoryProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckHistory.py"
)


# each case must start afresh and enforce the guarded runtime boundary
def RunHistoryCase(CaseName: str) -> dict[str, object]:
    ResultValue = RunProcess(
        (PythonExec, "-I", "-B", str(KHistoryProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert ResultValue.returncode == 0, ResultValue.stdout + ResultValue.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(ResultValue.stdout))
    assert ReportValue["case"] == CaseName
    assert ReportValue["runtime_external_accesses"] == 0
    return ReportValue
