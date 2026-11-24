import sys as System

import pytest as Pytest

from tests.Research.Supervisor.SupervisorAdaptiveTests import (
    CheckRealMinute as RunAdaptiveCase,
)


# windows growth needs a live resource sample while the controller still has waiting work
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinRamp() -> None:
    RunAdaptiveCase(RequireCpu=True)
