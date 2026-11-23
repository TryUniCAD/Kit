import sys
from pathlib import Path as FilePath
from subprocess import PIPE as KPipe, Popen as StartProcess, TimeoutExpired
from sysconfig import get_path as GetConfigPath

from pytest import mark as TestMark, raises as ExpectError

from tests.Research.Windows.Cli.OwnConsole import OwnConsole
from tests.Research.Windows.Cli.StopConsole import StopConsole
from tests.Research.Windows.Cli.StopCustody import StopCustody
from tests.Research.Windows.IsProcessAlive import IsProcessAlive
from tests.Research.Windows.WaitForExit import WaitForExit

if sys.platform == "win32":
    from subprocess import CREATE_NO_WINDOW as KNoWindow


# cleanup must recover pipe ownership from a surviving descendant after its real console leader exits
@TestMark.skipif(
    sys.platform != "win32", reason="Windows console custody process boundary"
)
def CheckLeaderExit(TmpPath: FilePath) -> None:
    if sys.platform == "win32":
        RootPath = FilePath(__file__).resolve().parents[4]
        RecordPath = TmpPath / "PipeChild"
        BasePython = str(getattr(sys, "_base_executable", sys.executable))
        Bootstrap = (
            "import site, sys, runpy; "
            + "site.addsitedir(sys.argv.pop(1)); "
            + "runpy.run_module(sys.argv.pop(1), run_name='__main__')"
        )
        with OwnConsole() as (JobName, JobHandle):
            _ = (TmpPath / "ConsoleCustody").write_text(JobName, encoding="utf-8")
            with StartProcess(
                [
                    BasePython,
                    "-c",
                    Bootstrap,
                    GetConfigPath("purelib"),
                    "tests.Research.Windows.Cli.ExitLeader",
                    str(RecordPath),
                ],
                cwd=RootPath,
                stdout=KPipe,
                stderr=KPipe,
                text=True,
                creationflags=KNoWindow,
            ) as Leader:
                try:
                    assert Leader.wait(timeout=45) == 0
                    ChildPid = int(RecordPath.read_text(encoding="utf-8"))
                    assert IsProcessAlive(ChildPid)
                    with ExpectError(TimeoutExpired):
                        _ = Leader.communicate(timeout=0.25)
                    StopCustody(JobHandle)
                    OutputText, ErrorText = Leader.communicate(timeout=15)
                    assert "retained stdout" in OutputText, (OutputText, ErrorText)
                    WaitForExit(ChildPid)
                finally:
                    try:
                        StopCustody(JobHandle)
                    finally:
                        StopConsole(Leader)
    else:
        raise OSError("Console custody process coverage requires Windows")
