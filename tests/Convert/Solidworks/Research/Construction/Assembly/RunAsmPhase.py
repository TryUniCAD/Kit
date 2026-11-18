from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# complete assembly evidence must cross fresh interpreter boundaries with runtime input guards and independent typed preparation instead of retaining constructed nodes
def RunAsmPhase(Request: dict[str, object], PhaseValue: str) -> dict[str, object]:
    ScriptsValue = {
        "build": "SdkAssemblyProcess.py",
        "prepare": "SdkAssemblyVerify.py",
        "counterpart": "SdkAssemblyCounterpart.py",
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
    return Report
