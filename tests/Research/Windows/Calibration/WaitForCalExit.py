from re import fullmatch as FullMatch
from typing import cast as CastValue

from tests.Research.Windows.Calibration.GetWinStart import GetWinStart
from tests.Research.Windows.WaitForExit import WaitForExit


# cleanup verification waits for the recorded process incarnation to exit
def WaitForCalExit(ProcessId: int, Started: str, *, Timeout: float = 15) -> None:
    if type(CastValue(object, ProcessId)) is not int or not 1 < ProcessId <= 0xFFFFFFFF:
        raise ValueError("invalid recorded calibration process ID")
    if type(CastValue(object, Started)) is not str:
        raise ValueError("invalid recorded calibration process creation time")
    Identity = FullMatch(r"windows:([1-9][0-9]{0,19})", Started)
    if Identity is None or int(Identity[1]) > 0xFFFFFFFFFFFFFFFF:
        raise ValueError("invalid recorded calibration process creation time")
    StartProbe = GetWinStart()

    # any failed identity query propagates because an unknown process cannot prove cleanup
    def IsSame(ObservedPid: int) -> bool:
        return StartProbe(ObservedPid) == Started

    WaitForExit(ProcessId, Timeout, IsAlive=IsSame)
