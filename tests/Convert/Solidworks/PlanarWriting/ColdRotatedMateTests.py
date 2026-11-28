from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# donor free construction and strict linked inspection must meet in a fresh process
def CheckColdMates() -> None:
    RootPath = FilePath(__file__).resolve().parents[4]
    WorkerPath = RootPath / "re/tooling/sw2026/rotated_mates/ProbeColdRotatedSuite.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(WorkerPath)),
        capture_output=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Report["construction_data_reads"] == 0
    assert Report["strict_modes"] == 2 and Report["relative_linked_reads"] == 1
    assert Report["deferred_modes"] == 1 and Report["matched_endpoints"] == 6
    assert Report["driver_mm"] == 52.125 and Report["public_writer_qualified"] is False
    assert Report["refused_class_shape"] == "coincident-distance-coincident"
