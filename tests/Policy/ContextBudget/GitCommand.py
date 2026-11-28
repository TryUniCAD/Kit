import os as SystemTools
import subprocess as ProcessTools
from pathlib import Path


# a private real repository must ignore machine git configuration and never consult credentials
def GitCommand(RootPath: Path, *Arguments: str) -> str:
    EnvValues = dict(SystemTools.environ)
    EnvValues.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": SystemTools.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        }
    )
    Result = ProcessTools.run(
        ["git", "-c", "core.hooksPath=" + str(RootPath / "NoHooks"), *Arguments],
        cwd=RootPath,
        env=EnvValues,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=30,
    )
    return Result.stdout
