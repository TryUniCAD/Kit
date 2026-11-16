from __future__ import annotations

from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# independent interpreters prevent current imports or cached graph state from supplying historical output
def RunPinned(
    Request: dict[str, object], SourceRoot: FilePath, IsCamera: bool
) -> dict[str, object]:
    ProgramPath = SourceRoot / (
        "re/tooling/sw2026/CameraProcess.py"
        if IsCamera
        else "tests/Convert/Solidworks/Research/FreshPartProcess.py"
    )
    Outcome = RunProcess(
        [PythonExec, "-I", "-B", str(ProgramPath), str(SourceRoot)],
        cwd=SourceRoot,
        input=DumpJson(Request),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Report["denied_reads"] == [] and Report["module_reads"]
    Streams = CastValue(dict[str, dict[str, object]], Report["streams"])
    assert len(Streams) == 8
    assert all(
        RowValue["passed"] and RowValue["tail"] == 0 for RowValue in Streams.values()
    )
    return Report
