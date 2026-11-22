from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec


# a fresh hosted interpreter checks the publication gate and reads an independently prepared two wall profile
def TestThinReg(TmpPath: FilePath) -> None:
    Program = FilePath(__file__).resolve().with_name("ThinRegPhase.py")
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Program)),
        cwd=TmpPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
