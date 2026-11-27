import json as JsonCodec
import os as OsLayer
import subprocess as Subprocess
import sys as System
from importlib import import_module as ImportModule
from pathlib import Path as FilePath
from types import ModuleType

from tests.Research.SessionRunner import ReadInput, WriteResult
from tests.Research.Supervisor.SessionRoot import SessionRoot
from tests.Research.SupervisorClient import KRepoRoot


# use an actual child process in place of the windows launcher and its job handle
class FixtureProcess:

    # the subprocess either reports a native fault or hangs until phase enforcement terminates it
    def __init__(
        self,
        Command: list[str],
        RootPath: FilePath,
        Environment: dict[str, str],
        Output: int,
        Error: int,
    ) -> None:
        super().__init__()
        _ = Environment
        setattr(self, "wait", self.WaitChild)
        setattr(self, "signal", self.KillChild)
        setattr(self, "finish", self.CheckExit)
        setattr(self, "close", self.CloseChild)
        ModeName = FilePath(Command[Command.index("-CasePath") + 1]).read_text(
            encoding="utf-8"
        )
        Program = {
            "rpc": "raise SystemExit(71)",
            "shutdown": "raise SystemExit(72)",
            "hung": "import time; time.sleep(120)",
            "ok": "raise SystemExit(0)",
        }[ModeName]
        self.Child = Subprocess.Popen(
            [System.executable, "-c", Program],
            cwd=RootPath,
            stdout=Output,
            stderr=Error,
        )

    # the real phase deadline must cover a launcher that never finishes
    def WaitChild(self, Timeout: float) -> int:
        return self.Child.wait(timeout=Timeout)

    # the fixture verifies hard stops go to the owned child
    def KillChild(self, Number: int) -> None:
        assert Number == 9
        self.Child.kill()

    # cleanup must observe process exit before permitting another claim
    def CheckExit(self) -> None:
        assert self.Child.poll() is not None

    # reap the fixture even if the code under test fails unexpectedly
    def CloseChild(self) -> None:
        if self.Child.poll() is None:
            self.Child.kill()
            _ = self.Child.wait(timeout=5)
            raise AssertionError("phase left its owned launcher running")


# exercise the production phase wrapper with unchanged staged bytes on every retry
def RunCapture() -> int:
    SessionPath = SessionRoot(System.argv[1])
    Packet = JsonCodec.loads((SessionPath / "job.json").read_text(encoding="utf-8"))
    Input = ReadInput(SessionPath, Packet["inputs"]["case"])
    assert Input == b"capture inputs"
    JobInfo = Packet["job"]
    ModeName = JobInfo["options"]["mode"]
    if Packet["attempt"] > 1 and ModeName != "always-rpc":
        ModeName = "ok"
    elif ModeName == "always-rpc":
        ModeName = "rpc"

    _ = OsLayer.environ.setdefault("SystemRoot", str(SessionPath))
    System.path.insert(0, str(KRepoRoot / "re/automation"))
    WindowsFixture = ModuleType("WindowsProcess")
    setattr(WindowsFixture, "WindowsProcess", FixtureProcess)
    System.modules["WindowsProcess"] = WindowsFixture
    Phase = ImportModule("CaptureTools.Catalogue.SolidWorks.RunSolidPhase")
    Recovery = ImportModule("CaptureTools.Catalogue.SolidWorks.SolidRecovery")
    WorkPath = SessionPath / "work"
    CasePath = WorkPath / "fixture.txt"
    _ = CasePath.write_text(ModeName, encoding="utf-8")
    try:
        Phase.RunSolidPhase(
            CasePath,
            WorkPath,
            {
                "interop_assembly": "fixture",
                "executable": "fixture",
                "phase_seconds": 1,
            },
            "first",
        )
    except Recovery.SolidRecovery as Fault:
        _ = System.stderr.write(str(Fault))
        return int(Fault.status)
    return WriteResult(SessionPath, JobInfo)


if __name__ == "__main__":
    System.exit(RunCapture())
