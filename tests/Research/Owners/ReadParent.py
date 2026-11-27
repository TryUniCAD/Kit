import os as OsLayer
import subprocess as Subprocess
import sys as System
from functools import cache as OncePerProcess
from pathlib import Path as FilePath

# the first wmi process query on a fresh runner exceeded the fifteen second warm budget
KColdQuerySeconds = 120


# owner checks need an independent parent observation to associate a gate with the supervisor
def ReadParent(ProcessId: int) -> int | None:
    if System.platform == "win32":
        WarmParent()
    Command = (
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(FilePath(__file__).with_suffix(".ps1")),
            str(ProcessId),
        ]
        if System.platform == "win32"
        else ["ps", "-p", str(ProcessId), "-o", "ppid="]
    )
    Result = Subprocess.run(
        Command, capture_output=True, text=True, check=False, timeout=15
    )
    if (
        Result.returncode == (3 if System.platform == "win32" else 1)
        and not Result.stdout.strip()
    ):
        return None
    assert Result.returncode == 0 and Result.stdout.strip().isdigit(), Result.stderr
    return int(Result.stdout.strip())


# the cold wmi provider start belongs outside the deadline of any owner observation
@OncePerProcess
def WarmParent() -> None:
    Result = Subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(FilePath(__file__).with_suffix(".ps1")),
            str(OsLayer.getpid()),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=KColdQuerySeconds,
    )
    assert Result.returncode == 0 and Result.stdout.strip().isdigit(), Result.stderr
