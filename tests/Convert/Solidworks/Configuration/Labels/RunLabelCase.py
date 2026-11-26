from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# native and authored label cases share one isolated archive decoder process
KLabelProbe = (
    FilePath(__file__).resolve().parents[5] / "re/tooling/sw2026/CheckCfgLabels.py"
)


# queue failures need the exact diagnostic from the guarded label decoder
def RunLabelCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KLabelProbe), CaseName),
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
