from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess

from tests.Research.Windows.WaitForExit import WaitForExit
from tests.Research.Windows.WaitForPids import WaitForPids


# successful cancellation needs prompt settlement and independent evidence that every owned worker exited
def AssertConsole(
    RootPath: FilePath, ResultInfo: CompletedProcess[str], SignalName: str
) -> None:
    assert ResultInfo.returncode == 0, (ResultInfo.stdout, ResultInfo.stderr)
    SignalInfo = LoadJson((RootPath / "Interrupted").read_text(encoding="utf-8"))
    assert SignalInfo["signal"] == SignalName
    ExitClock = float((RootPath / "LauncherExited").read_text(encoding="utf-8"))
    ElapsedTime = ExitClock - float(SignalInfo["at"])
    assert 0 <= ElapsedTime < 15, {"elapsed": ElapsedTime, "signal": SignalName}
    Events = [LoadJson(LineText) for LineText in ResultInfo.stdout.splitlines()]
    assert any(
        Event.get("event") == "finished"
        and Event["receipt"]["stop_reason"] == "supervisor_shutdown"
        for Event in Events
    ), Events
    for ProcessId in WaitForPids(RootPath / "ProcessIds.json"):
        WaitForExit(ProcessId)
