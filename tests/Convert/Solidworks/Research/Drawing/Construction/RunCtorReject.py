from json import dumps as DumpJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Research.Drawing.Construction.MakeCtorInput import (
    MakeCtorInput,
)


# unsupported neutral sheet choices must reject before any successful constructed document is returned
def RunCtorReject(ProbeName: str) -> None:
    RepoRoot = FilePath(__file__).resolve().parents[6]
    Outcome = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(RepoRoot / "re/tooling/sw2026/DrawingSheetConstructionProcess.py"),
        ],
        input=DumpJson(
            {
                "schema": "kit.sw2026.sdk-sheet-construction-process.v1",
                "request": MakeCtorInput("SdkSheetRejected", 9, 14),
                "qualification_probe": ProbeName,
            },
            sort_keys=True,
        ),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode != 0 and not Outcome.stdout
    assert "drawing sheet" in Outcome.stderr, Outcome.stderr
