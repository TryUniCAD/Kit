import subprocess as Subprocess
import sys as System

import pytest as Pytest

from tests.Research.Windows.Calibration.GetWinStart import GetWinStart
from tests.Research.Windows.Calibration.WaitForCalExit import WaitForCalExit


# an actual live process distinguishes a matching recorded owner from another creation identity
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckExitOwner() -> None:
    Process = Subprocess.Popen(
        (System.executable, "-I", "-B", "-c", "import sys; sys.stdin.buffer.read()"),
        stdin=Subprocess.PIPE,
    )
    Stream = Process.stdin
    try:
        assert Stream is not None
        Started = GetWinStart()(Process.pid)
        assert Started is not None
        OtherStart = f"windows:{int(Started.split(':')[1]) - 1}"
        WaitForCalExit(Process.pid, OtherStart, Timeout=0)
        with Pytest.raises(AssertionError, match=str(Process.pid)):
            WaitForCalExit(Process.pid, Started, Timeout=0)
        assert Process.poll() is None
    finally:
        try:
            if Stream is not None:
                Stream.close()
        finally:
            try:
                assert Process.wait(timeout=10) == 0
            except Subprocess.TimeoutExpired as TimeoutFailure:
                Process.kill()
                ExitCode = Process.wait(timeout=10)
                TimeoutFailure.add_note(
                    f"calibration fixture reaped with exit code {ExitCode}"
                )
                raise
    WaitForCalExit(Process.pid, Started)
