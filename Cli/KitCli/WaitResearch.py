from functools import partial as BindSignal
from signal import SIGINT, SIGTERM, getsignal as GetSignal, signal as SetSignal
from subprocess import Popen
from sys import platform as KPlatform

from KitCli.ForwardSignal import ForwardSignal


# waiting must preserve research cleanup while the launcher owns terminal signal delivery
def WaitResearch(ChildProcess: Popen[bytes]) -> int:
    SignalNumbers = []
    if KPlatform != "win32":
        from signal import SIGHUP

        SignalNumbers = [SIGINT, SIGTERM, SIGHUP]
    PreviousHandlers = {Number: GetSignal(Number) for Number in SignalNumbers}
    try:
        for SignalNumber in SignalNumbers:
            _ = SetSignal(SignalNumber, BindSignal(ForwardSignal, ChildProcess))
        while True:
            try:
                return ChildProcess.wait()
            except KeyboardInterrupt:
                continue
    finally:
        for SignalNumber, Handler in PreviousHandlers.items():
            _ = SetSignal(SignalNumber, Handler)
