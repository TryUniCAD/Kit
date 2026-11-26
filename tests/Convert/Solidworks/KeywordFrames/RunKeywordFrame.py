from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

# the command must resolve the checkout independently of the fixture working directory
KKeywordProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckKeywordFraming.py"
)


# each operation consumes only its own process inputs
def RunKeywordFrame(
    ModeName: str,
    SourcePath: FilePath,
    OutputPath: FilePath,
    ExtraArgs: tuple[str, ...] = (),
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KKeywordProbe),
            ModeName,
            str(SourcePath),
            str(OutputPath),
            *ExtraArgs,
        ],
        cwd=OutputPath.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
