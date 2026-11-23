from pathlib import Path as FilePath

from tests.Research.SupervisorClient import FixtureJob, SessionHost
from tests.Research.Windows.SetWinRunner import SetWinRunner


# both cancellation paths need the same real supervisor and independently recorded native worker tree
def PrepareCli(RootPath: FilePath) -> FilePath:
    Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
    SetWinRunner(Harness)
    Harness.SubmitJobs([
        FixtureJob(
            "windows:cli", "fixture.decode", lease_seconds=15,
            options={"mode": "hold", "pid_file": str(RootPath / "ProcessIds.json")},
        )
    ])
    return Harness.ConfigFile
