from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# independent guarded processes must verify construction preparation and mathematical agreement without sharing live archive objects
def RunCornerPhase(
    RequestValue: dict[str, object], PhaseValue: str
) -> dict[str, object]:
    ScriptNames = {
        "build": "SdkCornerProcess.py",
        "prepare": "SdkCornerPrepare.py",
        "counterpart": "SdkCornerCounterpart.py",
    }
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026" / ScriptNames[PhaseValue]),
            str(KRepoRoot),
        ),
        cwd=KRepoRoot,
        input=DumpJson(RequestValue),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["passed"] is True
    assert ReportValue["runtime_input_file_reads"] == 0
    assert (
        ReportValue["native_acceptance"]
        is ReportValue["public_writer_qualified"]
        is False
    )
    return ReportValue
