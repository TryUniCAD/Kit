from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# native header selection must run with the actual codec in a fresh process
KHeadLinkProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckCfgHeaderLink.py"
)


# the same process checks named stream selection map identity and malformed starts
def RunHeadLink(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KHeadLinkProbe), CaseName),
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
