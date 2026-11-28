from json import dumps as DumpJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Research.Drawing.Definition.MakeDefInput import (
    MakeDefInput,
)


# unsupported full document graphs must fail before a container or successful result is returned
def RunDefReject(ProbeName: str) -> None:
    RepoRoot = FilePath(__file__).resolve().parents[6]
    ScriptPath = RepoRoot / "re/tooling/sw2026/DrawingDefinitionProcess.py"
    Outcome = RunProcess(
        [PythonExec, "-I", "-B", str(ScriptPath)],
        input=DumpJson(
            {
                "schema": "kit.sw2026.sdk-drawing-definition-process.v1",
                "request": MakeDefInput("SdkRejectedDefinition", 2, 7),
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
    assert any(
        ErrorText in Outcome.stderr
        for ErrorText in (
            "blank drawing Definition",
            "drawing appearance state requires an embedded mapping",
            "unsupported SOLIDWORKS body class",
            "sheet body",
        )
    ), Outcome.stderr
