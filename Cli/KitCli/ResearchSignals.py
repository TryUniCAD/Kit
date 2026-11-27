from collections.abc import Iterator
from contextlib import contextmanager as ContextScope
from functools import partial as BindSignal
from signal import getsignal as GetSignal, signal as SetSignal
from subprocess import Popen

from KitCli.RouteSignalMut import RouteSignalMut
from KitCli.SelectSignals import SelectSignals


# signal ownership must precede spawning and restore callers even when process creation fails
@ContextScope
def ResearchSignals(
    OwnWindows: bool = False,
) -> Iterator[tuple[list[Popen[bytes]], list[int]]]:
    SignalNumbers = SelectSignals(OwnWindows)
    PendingSignals: list[int] = []
    ChildProcesses: list[Popen[bytes]] = []
    PreviousHandlers = {Number: GetSignal(Number) for Number in SignalNumbers}
    try:
        for SignalNumber in SignalNumbers:
            _ = SetSignal(
                SignalNumber, BindSignal(RouteSignalMut, ChildProcesses, PendingSignals)
            )
        yield ChildProcesses, PendingSignals
    finally:
        for SignalNumber, Handler in PreviousHandlers.items():
            _ = SetSignal(SignalNumber, Handler)
