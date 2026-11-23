from tests.Research.Supervisor.SupervisorAdaptiveTests import (
    CheckRealMinute as RunAdaptiveCase,
)


# windows growth needs a live resource sample while the controller still has waiting work
def CheckWinRamp() -> None:
    RunAdaptiveCase(RequireCpu=True)
