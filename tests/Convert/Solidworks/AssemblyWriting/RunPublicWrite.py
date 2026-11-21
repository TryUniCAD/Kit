from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# actual public registry processes verify bundle publication without replacing the adapter with a test implementation
def RunPublicWrite(
    ModeValue: str, CountValue: int, OutputPath: FilePath
) -> dict[str, object]:
    ScriptPath = KRepoRoot / "re/tooling/sw2026/PublicAssemblyRegistryProcess.py"
    Arguments = [
        PythonExec,
        "-I",
        "-B",
        str(ScriptPath),
        str(KRepoRoot),
        ModeValue,
        str(CountValue),
        str(OutputPath),
    ]
    ProcessValue = RunProcess(
        Arguments, cwd=KRepoRoot, capture_output=True, text=True, timeout=90
    )
    assert ProcessValue.returncode == 0, ProcessValue.stderr
    return CastValue(dict[str, object], LoadJson(ProcessValue.stdout))
