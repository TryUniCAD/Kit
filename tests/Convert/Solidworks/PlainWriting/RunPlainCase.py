from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument

# the fresh worker consumes a neutral request and exercises only the installed writer stack
KProjectRoot = FilePath(__file__).resolve().parents[4]


# two independent processes prevent shared writer state from hiding any input dependency
def RunPlainCase(DocumentValue: CadDocument) -> dict[str, object]:
    Command = KProjectRoot / "re/tooling/sw2026/CheckScopedPlainWriter.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Command), str(KProjectRoot)),
        input=DocumentValue.to_json(),
        capture_output=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["writer_input_file_reads"] == 0
    assert ReportValue["sdk_runtime_research_imports"] == 0
    return ReportValue
