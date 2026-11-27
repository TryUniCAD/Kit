from pathlib import Path as FilePath
from sys import platform as KPlatform

from pytest import mark as TestMark

from tests.Research.Windows.Cli.AssertConsole import AssertConsole
from tests.Research.Windows.Cli.PrepareCli import PrepareCli
from tests.Research.Windows.Cli.RunConsole import RunConsole


# operating system console delivery must cancel the installed launcher and settle its supervised process tree
@TestMark.skipif(KPlatform != "win32", reason="Native Windows console process boundary")
@TestMark.parametrize("EventName", ("CTRL_C_EVENT", "CTRL_BREAK_EVENT"))
def CheckNativeStop(TmpPath: FilePath, EventName: str) -> None:
    RootPath = TmpPath.resolve()
    ConfigPath = PrepareCli(RootPath)
    ResultInfo = RunConsole(ConfigPath, EventName)
    AssertConsole(RootPath, ResultInfo, EventName)
