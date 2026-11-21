from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# a fresh hosted interpreter must publish and read an independent two wall thin profile
def TestThinReg(TmpPath: FilePath) -> None:
    Program = FilePath(__file__).with_name("ThinRegPhase.py")
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Program), str(KRepoRoot), str(TmpPath)),
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
