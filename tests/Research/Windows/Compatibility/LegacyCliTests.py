from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath, platform as KPlatform

from pytest import mark as TestMark

from tests.Research.SupervisorClient import FixtureJob, SessionHost
from tests.Research.Windows.Compatibility.PrepareLegacy import PrepareLegacy
from tests.Research.Windows.Compatibility.ProveLegacy import ProveLegacy


# incompatible research checkouts must fail before a real queued job can acquire a lease
@TestMark.skipif(KPlatform != "win32", reason="Windows supervisor compatibility")
@TestMark.parametrize(
    "MarkerText", ("", "KWindowsCliProtocol = 2", "KWindowsCliProtocol = True")
)
def CheckLegacyCli(TmpPath: FilePath, MarkerText: str) -> None:
    Harness = SessionHost(TmpPath, {"decode": 1}, {"fixture.decode": "decode"})
    Harness.SubmitJobs(
        [FixtureJob("windows:legacy", "fixture.decode", lease_seconds=15)]
    )
    BeforeJob = Harness.ReadJob("windows:legacy")
    StatePath = TmpPath / "SupervisorState"
    BeforeState = sorted(StatePath.rglob("*"))
    RootPath = PrepareLegacy(TmpPath, MarkerText)
    ResultInfo = RunProcess(
        [
            str(FilePath(KPythonPath).with_name("kit.exe")),
            "research",
            "--root",
            str(RootPath),
            "supervisor",
            "--config",
            str(Harness.ConfigFile),
            "run",
            "--max-seconds",
            "1",
        ],
        cwd=TmpPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert ResultInfo.returncode == 1, (ResultInfo.stdout, ResultInfo.stderr)
    assert "update the selected --root research checkout" in ResultInfo.stderr
    assert Harness.ReadJob("windows:legacy") == BeforeJob
    assert sorted(StatePath.rglob("*")) == BeforeState
    ProveLegacy(Harness, RootPath)
