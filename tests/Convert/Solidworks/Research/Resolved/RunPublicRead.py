from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

from interchange import CadDocument
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# fresh processes must consume generated archive bytes through the normal public sdk reader
def RunPublicRead(InputPath: FilePath) -> CadDocument:
    Outcome = RunProcess(
        (
            PythonExec,
            "-B",
            "-m",
            "tests.Convert.Solidworks.Research.Resolved.PublicReadProcess",
            str(InputPath),
        ),
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CadDocument.from_json(Outcome.stdout)
