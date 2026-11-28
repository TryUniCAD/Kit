from pathlib import Path as FilePath
from subprocess import PIPE as PipeMode
from subprocess import Popen as OpenProc
from subprocess import run as RunProcess
from sys import executable as PythonExec


# concurrent import processes must not acquire the same project writer lease
def CheckPlanLease(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[3]
    assert (RootPath / "re/automation/Planning/Lease.py").read_text()
    ScriptText = (
        "import sys as System\nimport time as ClockTools\n"
        f"System.path.insert(0,{str(RootPath / 're/automation/Planning')!r})\n"
        "from Lease import project_lock as ProjectLock\n"
        "\n# needed to hold ownership while the competing process attempts admission\n"
        f"LeaseFile = ProjectLock({'Check' + TmpPath.name!r})\n"
        "print('locked',flush=True)\n"
        "ClockTools.sleep(30)\n"
    )
    OwnerProc = OpenProc(
        [PythonExec, "-c", ScriptText], stdout=PipeMode, stderr=PipeMode, text=True
    )
    try:
        assert OwnerProc.stdout is not None
        assert OwnerProc.stdout.readline().strip() == "locked"
        Contender = RunProcess(
            [PythonExec, "-c", ScriptText.replace("ClockTools.sleep(30)", "")],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        assert Contender.returncode != 0
    finally:
        OwnerProc.terminate()
        assert OwnerProc.wait(timeout=15) != 0
    Released = RunProcess(
        [PythonExec, "-c", ScriptText.replace("ClockTools.sleep(30)", "")],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert Released.returncode == 0, Released.stderr
    assert Released.stdout.strip() == "locked"
