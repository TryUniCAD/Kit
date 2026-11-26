from pathlib import Path as FilePath

from tests.Research.Windows.WaitForExit import WaitForExit
from tests.Research.Windows.WaitForPids import WaitForPids


# successful evidence must establish worker cleanup before fallback custody can hide a supervisor leak
def VerifyWorkers(RecordPath: FilePath) -> None:
    for ProcessId in WaitForPids(RecordPath):
        WaitForExit(ProcessId)
