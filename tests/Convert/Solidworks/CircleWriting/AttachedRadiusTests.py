from json import loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import KMeasureRoot


# a real reader process must reject linked radius metadata with an unqualified physical state
def TestLinkedRad() -> None:
    Command = KMeasureRoot / "re/tooling/sw2026/CheckLinkedRadiusQueue.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Command)),
        capture_output=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["permissive_compatibility"] is True
    assert ReportValue["strict_refusals"] == {
        "design": "active kernel transmit profile is unqualified",
        "geometry": "active kernel transmit profile is unqualified",
    }
