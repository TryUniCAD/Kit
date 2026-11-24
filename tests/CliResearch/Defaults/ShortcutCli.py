from os import environ as KEnvironment
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as KPythonPath


# the shortcut must work in an isolated interpreter without powershell profiles or shell functions
def ShortcutCli(
    Directory: FilePath, ConfigPath: FilePath, *Arguments: str
) -> CompletedProcess[str]:
    return RunProcess(
        (KPythonPath, "-I", "-m", "KitCli", *Arguments),
        cwd=Directory,
        env={**KEnvironment, "KIT_RUN_DEFAULTS": str(ConfigPath)},
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
