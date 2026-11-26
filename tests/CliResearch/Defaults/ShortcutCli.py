from os import environ as KEnvironment
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as KPythonPath


# the shortcut must work in an isolated interpreter without powershell profiles or shell functions
def ShortcutCli(
    Directory: FilePath, ConfigPath: FilePath, *Arguments: str, UseHome: bool = False
) -> CompletedProcess[str]:
    Environment = {
        **KEnvironment,
        "KIT_RUN_DEFAULTS": str(ConfigPath),
        "USERPROFILE": str(Directory),
        "HOME": str(Directory),
    }
    if UseHome:
        _ = Environment.pop("KIT_RUN_DEFAULTS")
    return RunProcess(
        (KPythonPath, "-I", "-m", "KitCli", *Arguments),
        cwd=Directory,
        env=Environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
