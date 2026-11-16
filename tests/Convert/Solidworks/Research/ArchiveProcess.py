from __future__ import annotations

from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

# repository resolution keeps child processes independent from the invoking working directory
KRepoRoot = FilePath(__file__).resolve().parents[4]

# an explicit native corpus keeps compatibility scope reproducible across environments
KCorpus = KRepoRoot / "re" / "solidworks" / "v2026" / "corpus" / "ladder"

# a fixed research entry point keeps subprocess evidence tied to the reviewed implementation
KScriptPath = KRepoRoot / "re" / "tooling" / "sw2026" / "serial" / "RoundTrip.py"


# isolated interpreters expose corpus compatibility failures at the command boundary
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
