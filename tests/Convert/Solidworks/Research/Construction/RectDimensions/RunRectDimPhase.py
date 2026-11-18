from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# construction typed preparation and independent mathematical comparison must use separate guarded processes without shared archive objects
def RunRectDimPhase(
    RequestValue: dict[str, object], PhaseValue: str
) -> dict[str, object]:
    ScriptsValue = {
        "build": "SdkRectDimProcess.py",
        "prepare": "SdkRectDimPrepare.py",
        "counterpart": "SdkRectDimCounterpart.py",
    }
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026" / ScriptsValue[PhaseValue]),
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
    assert (
        ReportValue["passed"] is True and ReportValue["runtime_input_file_reads"] == 0
    )
    assert (
        ReportValue["native_acceptance"]
        is ReportValue["public_writer_qualified"]
        is False
    )
    if PhaseValue != "counterpart":
        assert ReportValue["sdk_runtime_research_imports"] == 0
    return ReportValue
