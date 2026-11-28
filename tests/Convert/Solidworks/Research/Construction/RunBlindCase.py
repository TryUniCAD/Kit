from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# constructor evidence must traverse a fresh guarded process and complete sdk native stream writers
def RunBlindCase(Request: dict[str, object]) -> dict[str, object]:
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/SdkBlindEndProcess.py"),
            str(KRepoRoot),
        ),
        cwd=KRepoRoot,
        input=DumpJson(Request),
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Report["passed"] is Report["memory_roundtrip"] is True
    assert Report["runtime_input_file_reads"] == 0
    assert Report["native_acceptance"] is Report["public_writer_qualified"] is False
    return Report
