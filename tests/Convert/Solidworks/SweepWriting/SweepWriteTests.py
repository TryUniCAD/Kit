from json import loads as ReadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue


# the normal stream registry and direct writer must reproduce the measured sweep lifecycle in fresh processes
def TestSweepWrite() -> None:
    Repository = FilePath(__file__).resolve().parents[4]
    ScriptValue = Repository / "re/tooling/sw2026/CheckScopedSweep.py"
    ProcessValue = RunProcess(
        (PythonExe, "-I", "-B", str(ScriptValue)),
        cwd=Repository,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    assert ProcessValue.returncode == 0, ProcessValue.stderr
    ReportValue = CastValue(dict[str, object], ReadJson(ProcessValue.stdout))
    assert ReportValue["writer_processes"] == 2
    assert ReportValue["native_calls"] == 0
    for CaseValue in CastValue(list[dict[str, object]], ReportValue["cases"]):
        assert CaseValue["exact_registry_and_direct_streams"] is True
        assert CaseValue["native_transfers"] == 6
        assert CaseValue["normalized_state_checks"] == 30
        assert CaseValue["writer_runtime_input_reads"] == 0
        assert CaseValue["occupied_stream_and_unverified_path_refused"] is True
