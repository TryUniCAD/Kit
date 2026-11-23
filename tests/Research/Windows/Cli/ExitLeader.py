import sys
from os import _exit as ExitProcess
from pathlib import Path as FilePath
from subprocess import Popen as StartProcess
from time import monotonic as ReadClock, sleep as WaitSeconds
from typing import NoReturn

from tests.Research.Windows.Cli.JoinConsole import JoinConsole

if sys.platform == "win32":
    from subprocess import CREATE_NO_WINDOW as KNoWindow


# the custody witness must outlive its leader without relying on interpreter shutdown cleanup
def RunExitLeader() -> NoReturn:
    if sys.platform == "win32":
        RecordPath = FilePath(sys.argv[1])
        JoinConsole(RecordPath)
        ChildProcess = StartProcess(
            [sys.executable, "-m", "tests.Research.Windows.Cli.PipeChild", str(RecordPath)],
            stdout=sys.stdout,
            stderr=sys.stderr,
            creationflags=KNoWindow,
        )
        UntilTime = ReadClock() + 30
        while ReadClock() < UntilTime:
            if ChildProcess.poll() is not None:
                raise RuntimeError("Pipe descendant exited before its custody witness")
            try:
                if int(RecordPath.read_text(encoding="utf-8")) == ChildProcess.pid:
                    ExitProcess(0)
            except (OSError, ValueError):
                pass
            WaitSeconds(0.01)
        raise RuntimeError("Pipe descendant did not report readiness")
    else:
        raise OSError("Console custody process coverage requires Windows")


if __name__ == "__main__":
    RunExitLeader()
