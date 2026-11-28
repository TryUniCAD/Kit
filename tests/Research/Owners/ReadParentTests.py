import os as OsLayer
import subprocess as Subprocess
import sys as System

from tests.Research.Owners.ReadParent import ReadParent


# parent observation needs process boundary coverage on both supported host paths
def CheckParentPid() -> None:
    ChildProcess = Subprocess.Popen(
        [System.executable, "-c", "import time; time.sleep(30)"]
    )
    try:
        assert ReadParent(ChildProcess.pid) == OsLayer.getpid()
    finally:
        ChildProcess.terminate()
        assert ChildProcess.wait(timeout=15) is not None
    assert ReadParent(ChildProcess.pid) is None
    assert ReadParent(0xFFFFFFFF) is None
