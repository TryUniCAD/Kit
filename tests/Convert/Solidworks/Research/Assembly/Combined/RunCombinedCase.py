from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue


# guarded assembly construction must execute independently from the verifier
def RunCombinedCase(Request: dict[str, object], Failure: str = "") -> dict[str, object]:
    RootValue = FilePath(__file__).resolve().parents[6]
    Result = RunProcess(
        [
            PythonExe,
            "-I",
            "-B",
            str(RootValue / "re/tooling/sw2026/PlanarCombinedBundleProcess.py"),
        ],
        cwd=RootValue,
        input=DumpJson(Request),
        capture_output=True,
        text=True,
        check=False,
        timeout=40,
    )
    if Failure:
        assert Result.returncode != 0 and not Result.stdout and Failure in Result.stderr
        return {}
    assert Result.returncode == 0, Result.stderr
    return CastValue(dict[str, object], LoadJson(Result.stdout))
