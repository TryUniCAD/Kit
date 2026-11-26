import sys as System
from collections.abc import Callable
from functools import cache as CacheProbe
from runpy import run_path as RunPath
from typing import cast as CastValue

from tests.Research.SupervisorClient import KRepoRoot


# calibration checks use the same exact kernel identity as the recorded process owner
@CacheProbe
def GetWinStart() -> Callable[[int], str | None]:
    if System.platform != "win32":
        raise OSError("Windows calibration process identity requires a Windows host")
    PathValue = KRepoRoot / "re/automation/ApplicationWorkers/WindowsIdentity.py"
    return CastValue(
        Callable[[int], str | None], RunPath(str(PathValue))["process_start"]
    )
