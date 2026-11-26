from os import environ as Environment
from pathlib import Path as FilePath
from subprocess import CompletedProcess as ProcessResult
from subprocess import run as RunProcess
from sys import executable as PythonExe


# each parameter stage runs at its normal command boundary with explicit input and output paths
def RunParamStage(
    ScriptName: str,
    InputPath: FilePath,
    OutputPath: FilePath,
    *,
    ResearchFolder: str = "SavedParameterBindings",
) -> ProcessResult[str]:
    RootPath = FilePath(__file__).resolve().parents[5]
    Command = RootPath / "re/Fusion" / ResearchFolder / ScriptName
    return RunProcess(
        [PythonExe, "-B", str(Command), str(InputPath), str(OutputPath)],
        env=dict(Environment, PYTHONPATH=str(RootPath / "src")),
        cwd=OutputPath.parent,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
