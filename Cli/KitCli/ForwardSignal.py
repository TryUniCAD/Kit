from subprocess import Popen
from types import FrameType


# the launcher must deliver terminal and direct signals to its separate research session
def ForwardSignal(
    ChildProcess: Popen[bytes], SignalNumber: int, Frame: FrameType | None
) -> None:
    if ChildProcess.poll() is not None:
        return
    try:
        ChildProcess.send_signal(SignalNumber)
    except ProcessLookupError:
        return
