from json import dumps as DumpJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Research.Drawing.MakeSheetInput import MakeSheetInput


# unsupported drawing modes must abort the complete process before container output exists
def RunSheetReject(ProbeName: str) -> None:
    RepoRoot = FilePath(__file__).resolve().parents[5]
    ScriptPath = RepoRoot / "re/tooling/sw2026/SheetWriterProcess.py"
    Outcome = RunProcess(
        [PythonExec, "-I", "-B", str(ScriptPath)],
        input=DumpJson(
            {
                "schema": "kit.sw2026.sdk-sheet-writer-process.v1",
                "kind": "blank",
                "request": MakeSheetInput("SdkRejectedSheet", 1, 1),
                "qualification_probe": ProbeName,
            }
        ),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode != 0 and not Outcome.stdout
    assert "sheet body" in Outcome.stderr, Outcome.stderr
    assert "changed the output or native map" not in Outcome.stderr, Outcome.stderr
