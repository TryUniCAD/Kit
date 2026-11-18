from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# full candidate evidence must cross fresh guarded interpreter boundaries without retaining modeled nodes between construction preparation and independent comparison
def RunPartPhase(
    Request: dict[str, object], PhaseValue: str, ProfileValue: str = "rectangle"
) -> dict[str, object]:
    ScriptsValue = {
        "build": "SdkBlindPartProcess.py",
        "prepare": "SdkBlindPartPrepare.py",
        "counterpart": "SdkBlindPartCounterpart.py",
    }
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026" / ScriptsValue[PhaseValue]),
            str(KRepoRoot),
            *(("polygon",) if ProfileValue == "polygon" else ()),
        ),
        cwd=KRepoRoot,
        input=DumpJson(Request),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Report["passed"] is True and Report["runtime_input_file_reads"] == 0
    assert Report["native_acceptance"] is Report["public_writer_qualified"] is False
    if PhaseValue != "counterpart":
        assert Report["sdk_runtime_research_imports"] == 0
    return Report
