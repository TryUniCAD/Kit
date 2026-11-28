from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# each end condition must exercise the ordinary composer and linked reader in separate guarded processes
def RunCirclePhase(
    RequestValue: dict[str, object], PhaseValue: str
) -> dict[str, object]:
    Process = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/SdkCircleProof.py"),
            str(KRepoRoot),
            PhaseValue,
        ],
        cwd=KRepoRoot,
        input=DumpJson(RequestValue),
        text=True,
        capture_output=True,
        check=False,
        timeout=90,
    )
    assert Process.returncode == 0, Process.stderr
    return CastValue(dict[str, object], LoadJson(Process.stdout))
