from _thread import interrupt_main as InterruptMain
from pathlib import Path as FilePath
from signal import Signals

from tests.Research.Windows.Cli.WriteSignal import WriteSignal
from tests.Research.Windows.WaitForPids import WaitForPids


# cancellation must reach the launcher only after its real supervised process tree exists
def InterruptReady(RecordPath: FilePath, SignalName: str) -> None:
    _ = WaitForPids(RecordPath)
    WriteSignal(RecordPath, SignalName)
    InterruptMain(Signals[SignalName])
