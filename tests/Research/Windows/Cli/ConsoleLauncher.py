from pathlib import Path as FilePath
from sys import argv as KArguments
from threading import Thread

from KitCli.MainEntry import MainEntry
from tests.Research.Windows.Cli.InterruptReady import InterruptReady
from tests.Research.Windows.Cli.JoinConsole import JoinConsole


# a private console keeps native control events isolated from the test runner and desktop
def LaunchConsole() -> int:
    RecordName, RootName, ConfigName, SignalName = KArguments[1:]
    JoinConsole(FilePath(RecordName))
    Watcher = Thread(
        target=InterruptReady,
        args=(FilePath(RecordName), SignalName),
        daemon=True,
    )
    KArguments[:] = [
        "kit",
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
    Watcher.start()
    return MainEntry()


if __name__ == "__main__":
    raise SystemExit(LaunchConsole())
