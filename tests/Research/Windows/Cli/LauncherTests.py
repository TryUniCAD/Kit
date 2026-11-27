from pathlib import Path as FilePath
from sys import platform as KPlatform

from pytest import mark as TestMark

from tests.Research.Windows.Cli.AssertConsole import AssertConsole
from tests.Research.Windows.Cli.PrepareCli import PrepareCli
from tests.Research.Windows.Cli.RunConsole import RunConsole


# installed launcher cancellation must settle real supervisor receipts and retire every bound worker process
@TestMark.skipif(KPlatform != "win32", reason="Windows CLI process boundary")
@TestMark.parametrize("SignalName", ("SIGINT", "SIGTERM", "SIGBREAK"))
def CheckCliStop(TmpPath: FilePath, SignalName: str) -> None:
    RootPath = TmpPath.resolve()
    ConfigPath = PrepareCli(RootPath)
    ResultInfo = RunConsole(ConfigPath, SignalName)
    AssertConsole(RootPath, ResultInfo, SignalName)
