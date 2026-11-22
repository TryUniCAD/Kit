from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# native property controls are shared with the other solidworks archive cases
KProjectPath = FilePath(__file__).resolve().parents[4]

# separate processes read the exact committed cad inputs from the controlled corpus
KPartCorpus = KProjectPath / "re/solidworks/v2026/corpus"

# binary and write evidence runs through focused host process entrypoints
KPartProbe = KProjectPath / "re/tooling/sw2026/part_text"


# the queue invokes each complete workflow in its own interpreter
def RunPartText(WorkerPath: FilePath, *SourcePaths: FilePath) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(WorkerPath), *map(str, SourcePaths)),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(dict[str, object], LoadJson(Outcome.stdout))
