from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as Interpreter
from typing import cast as CastValue


# measured profiles must match their entire inspected archive or refuse even when logical streams agree
def TestRevEndMeas() -> None:
    RootValue = FilePath(__file__).resolve().parents[4]
    Worker = RootValue / "re/tooling/sw2026/revolve/EndModes/ProveAggregateRevEnds.py"
    for CaseValue, DriversValue in (
        ("EndSingle", ["D1"]),
        ("EndMidplane", ["D1"]),
        ("EndTwo", ["D1", "D2"]),
        ("EndTwoReverse", ["D1", "D2"]),
    ):
        Result = RunProcess(
            (Interpreter, "-I", "-B", str(Worker), "--case", CaseValue),
            check=False,
            capture_output=True,
            text=True,
            cwd=RootValue,
            timeout=30,
        )
        assert Result.returncode == 0 and not Result.stderr, Result.stderr
        Report = CastValue(dict[str, object], LoadJson(Result.stdout))
        assert Report["name"] == CaseValue and Report["drivers"] == DriversValue
        assert len(CastValue(dict[str, str], Report["streams"])) == 10
        assert Report["runtime_input_reads"] == 0 and Report["native_processes"] == 0
        if Report["candidate_sha256"] == Report["measured_sha256"]:
            assert Report["publications"] == 3 and Report["refusals"] == 20
        else:
            assert Report["publications"] == 0 and Report["refusals"] == 23
