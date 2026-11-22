import time as TimeClock
from collections.abc import Callable

from tests.Research.Windows.IsProcessAlive import IsProcessAlive


# termination checks must allow asynchronous kernel cleanup before declaring that a process escaped
def WaitForExit(
    ProcessId: int,
    Timeout: float = 15,
    *,
    IsAlive: Callable[[int], bool] = IsProcessAlive,
) -> None:
    UntilTime = TimeClock.monotonic() + Timeout
    while IsAlive(ProcessId) and TimeClock.monotonic() < UntilTime:
        TimeClock.sleep(0.05)
    assert not IsAlive(ProcessId), ProcessId
