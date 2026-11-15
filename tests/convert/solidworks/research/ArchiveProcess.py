from __future__ import annotations

from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

KRepoRoot = FilePath(__file__).resolve().parents[4]
KCorpus = KRepoRoot / "re" / "solidworks" / "v2026" / "corpus" / "ladder"
KScriptPath = KRepoRoot / "re" / "tooling" / "sw2026" / "serial" / "RoundTrip.py"


def RunArchive(
    Pattern: str, StreamNames: str, ExtraArgs: tuple[str, ...] = ()
) -> CompletedProcess[str]:
    return RunProcess(
        [PythonExec, str(KScriptPath), Pattern, StreamNames, "-v", *ExtraArgs],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
