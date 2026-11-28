from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# recursive constructor verification must cross a fresh process with its own runtime read guard and complete typed stream round trips
def RunNestedPhase(Request: dict[str, object]) -> dict[str, object]:
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/SdkNestedAssemblyProcess.py"),
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
    assert Report["sdk_runtime_research_imports"] == 0
    assert Report["native_acceptance"] is Report["public_writer_qualified"] is False
    return Report
