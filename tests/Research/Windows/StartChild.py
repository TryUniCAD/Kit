import signal as Signals
import os as OsLayer
import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.Windows.BindChild import BindChild


# tree cleanup checks need a bound descendant that stays alive until the owner retires it
def StartChild(SessionPath: FilePath, Options: dict[str, str]) -> None:
    if System.platform != "win32":
        raise OSError("Windows child fixture requires a Windows host")
    _ = Signals.signal(int(getattr(Signals, "SIGBREAK")), Signals.SIG_IGN)
    if (
        SessionPath.parent.name != "sessions"
        or SessionPath.parents[1].name != "SupervisorState"
    ):
        raise ValueError("unexpected Windows fixture session layout")
    RecordPath = SessionPath.parents[2] / "ProcessIds.json"
    if FilePath(Options["pid_file"]) != RecordPath:
        raise ValueError("unexpected Windows fixture process record")
    ChildProcess = Subprocess.Popen(
        [
            System.executable,
            "-m",
            "tests.Research.Windows.WindowsRunner",
            "child",
            str(OsLayer.getpid()),
        ],
        creationflags=int(getattr(Subprocess, "CREATE_NEW_PROCESS_GROUP")),
    )
    UntilTime = TimeClock.monotonic() + 10
    Observation: dict[str, int] = {}
    JobName = ""
    while True:
        try:
            Observation = JsonCodec.loads(
                (SessionPath / "work/ChildReady.json").read_text(encoding="utf-8")
            )
            JobName = JsonCodec.loads(
                (SessionPath / "session.json").read_text(encoding="utf-8")
            )["job_object"]
            break
        except (OSError, ValueError):
            if TimeClock.monotonic() >= UntilTime:
                raise RuntimeError("child did not report readiness") from None
            TimeClock.sleep(0.01)
    assert ChildProcess.poll() is None
    ProcessIds = BindChild(ChildProcess.pid, OsLayer.getpid(), Observation, JobName)
    _ = RecordPath.write_text(JsonCodec.dumps(ProcessIds), encoding="utf-8")
    if Options["mode"] == "hold":
        TimeClock.sleep(120)
