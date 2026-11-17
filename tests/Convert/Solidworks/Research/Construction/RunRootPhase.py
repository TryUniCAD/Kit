from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# separate interpreters must construct and prepare native root streams without sharing cached model objects
def RunRootPhase(Request: dict[str, object], IsPrepare: bool) -> dict[str, object]:
    ScriptName = "SdkPartRootPrepare.py" if IsPrepare else "SdkPartRootProcess.py"
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
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Report["passed"] is True and Report["runtime_input_file_reads"] == 0
    assert (
        Report["native_acceptance"]
        is Report["public_writer_qualified"]
        is Report["full_part_factory"]
        is False
    )
    return Report
