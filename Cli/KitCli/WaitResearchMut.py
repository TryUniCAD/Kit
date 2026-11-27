from subprocess import Popen, TimeoutExpired
from sys import platform as KPlatform

from KitCli.ForwardSignal import ForwardSignal


# waiting must preserve research cleanup while the launcher owns terminal signal delivery
def WaitResearchMut(
    ChildProcess: Popen[bytes],
    PendingSignals: list[int],
) -> int:
    while PendingSignals:
        ForwardSignal(ChildProcess, PendingSignals.pop(0), None)
    while True:
        try:
            return ChildProcess.wait(timeout=0.1 if KPlatform == "win32" else None)
        except (KeyboardInterrupt, TimeoutExpired):
            continue
