from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

# repository resolution gives the definition worker a separate empty directory
KRepoRoot = FilePath(__file__).resolve().parents[4]


# the queue must exercise the same guarded process boundary for authors and readers
def RunDefProcess(TmpPath: FilePath, ModeValue: str, InputValue: bytes) -> bytes:
    ScriptPath = KRepoRoot / "re/tooling/sw2026/definition/ProveOrdinaryPartDef.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(ScriptPath), "--worker", ModeValue),
        input=InputValue,
        cwd=TmpPath,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stderr.decode("utf-8", errors="replace")
    assert list(TmpPath.iterdir()) == []
    return Outcome.stdout
