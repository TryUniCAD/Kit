import sys as System
from pathlib import Path as FilePath

from tests.Research.Windows.Cli.WriteSignal import WriteSignal
from tests.Research.Windows.WaitForPids import WaitForPids

if System.platform == "win32":
    from signal import CTRL_BREAK_EVENT as KBreakEvent, CTRL_C_EVENT as KCtrlEvent
    from win32api import GenerateConsoleCtrlEvent


# real console events must reach the installed launcher without directly cancelling its separate supervisor group
def SignalConsole(RecordPath: FilePath, EventName: str, GroupNumber: int) -> None:
    if System.platform != "win32":
        raise OSError("Native console delivery requires Windows")
    _ = WaitForPids(RecordPath)
    if EventName == "CTRL_C_EVENT":
        EventCode, TargetGroup = KCtrlEvent, 0
    elif EventName == "CTRL_BREAK_EVENT":
        EventCode, TargetGroup = KBreakEvent, GroupNumber
    else:
        raise ValueError("Unknown Windows console event")
    WriteSignal(RecordPath, EventName)
    GenerateConsoleCtrlEvent(EventCode, TargetGroup)
