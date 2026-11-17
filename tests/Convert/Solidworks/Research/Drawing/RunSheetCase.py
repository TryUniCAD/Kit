from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# fresh processes verify the complete drawing pipeline rather than individual field helpers
def RunSheetCase(KindName: str, Request: dict[str, object]) -> dict[str, object]:
    RepoRoot = FilePath(__file__).resolve().parents[5]
    ScriptPath = RepoRoot / "re/tooling/sw2026/SheetWriterProcess.py"
    Outcome = RunProcess(
        [PythonExec, "-I", "-B", str(ScriptPath)],
        input=DumpJson(
            {
                "schema": "kit.sw2026.sdk-sheet-writer-process.v1",
                "kind": KindName,
                "request": Request,
            }
        ),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(dict[str, object], LoadJson(Outcome.stdout))
