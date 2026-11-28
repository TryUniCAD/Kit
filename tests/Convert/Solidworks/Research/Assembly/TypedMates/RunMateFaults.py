from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# malformed linked graphs must reach the real public reader as independent physical diagnostic copies
def RunMateFaults(
    ParentPath: FilePath,
    ChildPath: FilePath,
    WrongChild: FilePath,
    OutputPath: FilePath,
) -> tuple[dict[str, object], ...]:
    Outcome = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/PrepareMateReadFaults.py"),
            "--root",
            str(KRepoRoot),
            "--parent",
            str(ParentPath),
            "--child",
            str(ChildPath),
            "--wrong-child",
            str(WrongChild),
            "--output",
            str(OutputPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Manifest = CastValue(
        dict[str, object], LoadJson((OutputPath / "Faults.json").read_bytes())
    )
    assert (
        Manifest["writer_output_count"] == 0
        and Manifest["diagnostic_output_count"] == 14
    )
    return tuple(CastValue(list[dict[str, object]], Manifest["cases"]))
