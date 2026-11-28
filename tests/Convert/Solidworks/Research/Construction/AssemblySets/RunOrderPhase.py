from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Construction.Assembly.RunAsmPhase import (
    RunAsmPhase,
)


# ordered construction and rejection must cross fresh guarded process boundaries while sharing the independent complete stream verifier and mathematical counterpart
def RunOrderPhase(Request: dict[str, object], PhaseValue: str) -> dict[str, object]:
    if PhaseValue in ("prepare", "counterpart"):
        return RunAsmPhase(Request, PhaseValue)
    ScriptName = (
        "SdkOrderedAssemblyProcess.py"
        if PhaseValue == "build"
        else "SdkOrderedFaultProcess.py"
    )
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026" / ScriptName),
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
