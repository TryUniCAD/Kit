from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# the process fixture must locate the checkout without relying on its working directory
KKeywordWorker = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckKeywordModel.py"
)


# separate interpreters keep the wire contract independent of caller imports and state
def RunKeyModel(ModeName: str, InputData: bytes) -> CompletedProcess[bytes]:
    return RunProcess(
        [PythonExec, "-I", "-B", str(KKeywordWorker), ModeName],
        input=InputData,
        capture_output=True,
        check=False,
        timeout=60,
    )


# compare independent wire bytes before asking the existing parser to describe the output
def ReadKeyModel(InputValue: dict[str, object], WireValue: bytes) -> dict[str, object]:
    Written = RunKeyModel("write", DumpJson(InputValue).encode("utf-8"))
    assert Written.returncode == 0, Written.stderr
    assert Written.stdout == WireValue
    ReadBack = RunKeyModel("read", Written.stdout)
    assert ReadBack.returncode == 0, ReadBack.stderr
    return CastValue(dict[str, object], LoadJson(ReadBack.stdout))
