from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue


# isolated child processes attest to definition construction and preparation without file reads
def RunDefProcess(JobsValue: list[dict[str, object]]) -> list[dict[str, object]]:
    RootValue = FilePath(__file__).resolve().parents[5]
    Result = RunProcess(
        [
            PythonExe,
            "-I",
            "-B",
            str(RootValue / "re/tooling/sw2026/ModelDefinitionProcess.py"),
        ],
        cwd=RootValue,
        input=DumpJson(JobsValue).encode("utf-8"),
        capture_output=True,
        check=True,
        timeout=30,
    )
    return CastValue(list[dict[str, object]], LoadJson(Result.stdout))
