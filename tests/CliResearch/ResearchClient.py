from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as KPythonPath, platform as KPlatform
from os import environ as KEnvironment

from tests.CliResearch.ResearchRoot import ResearchRoot


# compatibility checks must exercise the installed bridge against the explicitly pinned research checkout
def ResearchCli(
    WorkPath: FilePath,
    ToolName: str,
    *Arguments: str,
    Checkout: FilePath | None = None,
) -> CompletedProcess[str]:
    return RunProcess(
        (
            str(
                FilePath(KPythonPath).with_name(
                    "kit.exe" if KPlatform == "win32" else "kit"
                )
            ),
            "research",
            "--root",
            str(ResearchRoot() if Checkout is None else Checkout),
            ToolName,
            *Arguments,
        ),
        cwd=WorkPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        env={**KEnvironment, "KIT_NATIVE_API_DIRECTORY": str(WorkPath / "NativeApi")},
    )
