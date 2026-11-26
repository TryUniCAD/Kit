from pathlib import Path as FilePath
from subprocess import CompletedProcess, Popen
from time import monotonic as ReadClock

from tests.Research.Windows.Cli.StopConsole import StopConsole
from tests.Research.Windows.Cli.StopCustody import StopCustody
from tests.Research.Windows.Cli.VerifyWorkers import VerifyWorkers


# shared capture must release owned pipe descendants even when their console leader has exited
def CaptureConsole(
    ConsoleProcess: Popen[str],
    JobHandle: int,
    WorkPath: FilePath,
    Timeout: float = 90,
) -> CompletedProcess[str]:
    try:
        OutputText, ErrorText = ConsoleProcess.communicate(timeout=Timeout)
        _ = (WorkPath / "LauncherExited").write_text(str(ReadClock()), encoding="utf-8")
        if ConsoleProcess.returncode == 0:
            VerifyWorkers(WorkPath / "ProcessIds.json")
        return CompletedProcess(
            ConsoleProcess.args, ConsoleProcess.returncode, OutputText, ErrorText
        )
    finally:
        try:
            StopCustody(JobHandle)
        finally:
            StopConsole(ConsoleProcess)
