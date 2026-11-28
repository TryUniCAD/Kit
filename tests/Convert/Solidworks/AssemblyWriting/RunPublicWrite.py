from json import loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# guarded processes exercise the registry and complete measured fixture without the cad oracle
def RunPublicWrite(ModeValue: str) -> dict[str, object]:
    ScriptPath = KRepoRoot / "re/tooling/sw2026/MeasuredPlanarPublicationProcess.py"
    ProcessValue = RunProcess(
        (PythonExec, "-I", "-B", str(ScriptPath), ModeValue),
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert ProcessValue.returncode == 0, ProcessValue.stderr
    Report = CastValue(dict[str, object], LoadJson(ProcessValue.stdout))
    assert Report["passed"] is True
    assert Report["runtime_input_file_reads"] == 0
    assert Report["native_processes_started"] == 0
    return Report
