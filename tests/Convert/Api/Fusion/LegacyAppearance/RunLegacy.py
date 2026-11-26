from os import environ as Environment, pathsep as PathSeparator
from pathlib import Path as FilePath
from subprocess import CompletedProcess as ProcessResult, run as RunProcess
from sys import executable as PythonExe


# a fresh interpreter isolates each actual property writer invocation
def RunLegacy(Request: FilePath, Output: FilePath) -> ProcessResult[str]:
    RootPath = FilePath(__file__).resolve().parents[5]
    SearchPath = PathSeparator.join(
        (str(RootPath / "src"), str(RootPath / "re/Fusion/LegacyBodyAppearance"))
    )
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(FilePath(__file__).with_name("LegacyChild.py")),
            str(Request),
            str(Output),
        ],
        env=dict(Environment, PYTHONPATH=SearchPath),
        cwd=Request.parent,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
