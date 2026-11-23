from pathlib import Path as FilePath
from time import monotonic as ReadClock, sleep as WaitSeconds


# the native observer must use the actual console root rather than a redirected interpreter identifier
def WaitConsole(RecordPath: FilePath) -> int:
    UntilTime = ReadClock() + 30
    while ReadClock() < UntilTime:
        try:
            GroupNumber = int(RecordPath.with_name("ConsoleGroup").read_text(encoding="utf-8"))
            if GroupNumber > 1:
                return GroupNumber
        except (OSError, ValueError):
            pass
        WaitSeconds(0.01)
    raise RuntimeError("Console owner did not publish its native process group")
