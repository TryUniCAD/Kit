import sys
from pathlib import Path as FilePath
from subprocess import Popen as StartProcess

from tests.Research.Windows.Cli.CanIgnoreEvent import CanIgnoreEvent
from tests.Research.Windows.Cli.SignalConsole import SignalConsole
from tests.Research.Windows.Cli.StopConsole import StopConsole
from tests.Research.Windows.Cli.WaitConsole import WaitConsole

if sys.platform == "win32":
    from win32api import SetConsoleCtrlHandler


# native events must exercise the installed executable while the observer owns only the private console
def LaunchNative() -> int:
    if sys.platform == "win32":
        RecordName, RootName, ConfigName, EventName = sys.argv[1:]
        RecordPath = FilePath(RecordName)
        GroupNumber = WaitConsole(RecordPath)
        KitExecutable = FilePath(sys.executable).with_name("kit.exe")
        SetConsoleCtrlHandler(CanIgnoreEvent, True)
        try:
            with StartProcess(
                [
                    str(KitExecutable),
                    "research",
                    "--root",
                    RootName,
                    "supervisor",
                    "--config",
                    ConfigName,
                    "run",
                    "--max-seconds",
                    "60",
                ]
            ) as Launcher:
                try:
                    SignalConsole(RecordPath, EventName, GroupNumber)
                    return Launcher.wait(timeout=75)
                finally:
                    StopConsole(Launcher)
        finally:
            SetConsoleCtrlHandler(CanIgnoreEvent, False)
    else:
        raise OSError("Native console coverage requires Windows")


if __name__ == "__main__":
    raise SystemExit(LaunchNative())
