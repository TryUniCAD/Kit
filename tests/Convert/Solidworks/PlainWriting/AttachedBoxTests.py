from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as Interpreter


# the isolated source conversion keeps file stream cache tracking intact for plain parts
def TestAttachedBox() -> None:
    RootValue = FilePath(__file__).resolve().parents[4]
    Worker = (
        RootValue / "re/tooling/sw2026/attached_top_box_source/CheckMainBoxQueueCase.py"
    )
    Result = RunProcess(
        [Interpreter, "-I", "-B", str(Worker)],
        cwd=RootValue,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert Result.returncode == 0, Result.stderr
