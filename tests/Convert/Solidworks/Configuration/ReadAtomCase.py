from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# both disclosed atom sources must use the real archive reader in fresh processes
KAtomProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckCfgAtoms.py"
)


# the queue needs runtime guard evidence and diagnostics from the archive process
def ReadAtomCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KAtomProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["runtime_external_accesses"] == 0
    assert ReportValue["inherited_slots"] == [1, 2, 3]
    assert ReportValue["body_kind"] == 0
    return ReportValue
