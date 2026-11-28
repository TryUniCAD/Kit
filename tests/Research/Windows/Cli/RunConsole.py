import sys
from pathlib import Path as FilePath
from subprocess import PIPE as KPipe, CompletedProcess, Popen as StartProcess
from sys import executable as KPythonPath

from tests.Research.Windows.Cli.CaptureConsole import CaptureConsole
from tests.Research.Windows.Cli.OwnConsole import OwnConsole

if sys.platform == "win32":
    from subprocess import CREATE_NEW_CONSOLE as KNewConsole
    from subprocess import STARTF_USESHOWWINDOW as KUseShowWindow
    from subprocess import STARTUPINFO as StartupInfo


# native cancellation evidence requires an actual hidden console shared by launcher and supervisor
def RunConsole(ConfigPath: FilePath, SignalName: str) -> CompletedProcess[str]:
    if sys.platform == "win32":
        RootPath = FilePath(__file__).resolve().parents[4]
        WindowInfo = StartupInfo()
        setattr(WindowInfo, "dwFlags", KUseShowWindow)
        setattr(WindowInfo, "wShowWindow", 0)
        ModuleName = (
            "NativeConsole" if SignalName.startswith("CTRL_") else "ConsoleLauncher"
        )
        Arguments = [
            KPythonPath,
            "-m",
            "tests.Research.Windows.Cli." + ModuleName,
            str(ConfigPath.parent / "ProcessIds.json"),
            str(RootPath),
            str(ConfigPath),
            SignalName,
        ]
        with OwnConsole() as (JobName, JobHandle):
            _ = (ConfigPath.parent / "ConsoleCustody").write_text(
                JobName, encoding="utf-8"
            )
            with StartProcess(
                Arguments,
                cwd=RootPath,
                creationflags=KNewConsole,
                startupinfo=WindowInfo,
                stdout=KPipe,
                stderr=KPipe,
                text=True,
            ) as ConsoleProcess:
                return CaptureConsole(
                    ConsoleProcess, JobHandle, ConfigPath.parent, Timeout=210
                )
    else:
        raise OSError("Windows CLI console coverage requires a Windows host")
