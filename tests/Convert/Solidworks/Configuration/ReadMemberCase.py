from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# member records must pass through a fresh process with the actual archive codec
KMemberProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckCfgMembers.py"
)


# both member process cases call the same isolated archive reader
def ReadMemberCase(
    CaseName: str,
) -> tuple[dict[str, object], dict[str, object], list[str]]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KMemberProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    RelValue, ColorValue = CastValue(list[dict[str, object]], ReportValue["members"])
    Refusals = CastValue(list[str], ReportValue["refusals"])
    return RelValue, ColorValue, Refusals
