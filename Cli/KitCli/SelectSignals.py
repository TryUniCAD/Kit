import sys
from signal import SIGINT, SIGTERM

if sys.platform == "win32":
    from signal import SIGBREAK as KBreakSignal
else:
    from signal import SIGCONT, SIGHUP, SIGQUIT, SIGTSTP, SIGUSR1, SIGUSR2


# platform signal ownership must preserve ordinary windows readers while enabling supervised cancellation
def SelectSignals(OwnWindows: bool) -> list[int]:
    if sys.platform == "win32":
        if not OwnWindows:
            return []
        return [SIGINT, SIGTERM, KBreakSignal]
    else:
        return [SIGINT, SIGTERM, SIGHUP, SIGQUIT, SIGUSR1, SIGUSR2, SIGTSTP, SIGCONT]
