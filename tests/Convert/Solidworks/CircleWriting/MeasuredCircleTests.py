from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.CircleWriting.MakeCircleDoc import MakeCircleDoc
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import KMeasureRoot


# the hosted integration uses real writer boundaries and strict readback in a fresh audited process
def TestCircleWrite() -> None:
    Command = KMeasureRoot / "re/tooling/sw2026/CheckMeasuredCircleWriter.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Command), "--worker"),
        input=DumpJson(LoadJson(MakeCircleDoc().to_json())),
        capture_output=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["runtime_input_file_reads"] == 0
    assert ReportValue["profile_owners_verified"] is True
    assert ReportValue["stream_count"] == 10
