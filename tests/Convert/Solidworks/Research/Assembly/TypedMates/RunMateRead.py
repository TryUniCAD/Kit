from json import dumps as DumpJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec
from collections.abc import Mapping

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# public mate reads need a fresh interpreter so component discovery and validation cannot reuse live graph state
def RunMateRead(
    SourcePath: FilePath,
    Options: Mapping[str, object] | None = None,
    AdapterValues: Mapping[str, object] | None = None,
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/PublicMateReadProcess.py"),
            "--root",
            str(KRepoRoot),
        ],
        cwd=KRepoRoot,
        input=DumpJson(
            {
                "path": str(SourcePath),
                "options": dict(Options or {}),
                "adapter_values": (
                    dict(AdapterValues) if AdapterValues is not None else None
                ),
            }
        ),
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
