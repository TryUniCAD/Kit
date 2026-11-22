from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# the queue exercises retained native rows and independent roundoff through the real geometry reader
def TestShellParts() -> None:
    ProbePath = (
        FilePath(__file__).resolve().parents[4]
        / "re/tooling/sw2026/shell_source/CheckShellReadParts.py"
    )
    Result = RunProcess(
        (PythonExec, "-I", "-B", str(ProbePath), "measure"),
        capture_output=True,
        timeout=95,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr.decode()
    Report = CastValue(dict[str, dict[str, object]], LoadJson(Result.stdout))
    assert set(Report) == {"history", "rounding"}
    History = Report["history"]
    assert History["marks"] == [13, 10, 3, 1]
    assert History["body_slots"] == [2, 2, 0, 0]
    assert History["retained_rows"] == [6, 44, 32, 35]
    assert History["delete_only_control_marks"] == [7, 3]
    assert "actual controller" in str(History["other_controller_refused"])
    Rounding = Report["rounding"]
    assert Rounding["complete_topology"] == [11, 24, 16]
    _, NearValue, FarValue = CastValue(list[float], Rounding["extent_differences_mm"])
    assert 0 < NearValue <= CastValue(float, Rounding["tolerance_mm"]) < FarValue
    assert "matching footprint position" in str(Rounding["out_of_budget_refusal"])
    assert all(Value["runtime_data_reads"] == 0 for Value in Report.values())


# the queue exercises fresh public history on a separately modeled rectangular shell
def TestColdShell() -> None:
    ProbePath = (
        FilePath(__file__).resolve().parents[4]
        / "re/tooling/sw2026/shell_source/CheckColdShellRead.py"
    )
    Result = RunProcess(
        (PythonExec, "-I", "-B", str(ProbePath), "--model"),
        capture_output=True,
        timeout=95,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr.decode()
    Report = CastValue(dict[str, object], LoadJson(Result.stdout))
    Cases = CastValue(dict[str, dict[str, object]], Report["cases"])
    (CaseValue,) = Cases.values()
    FullRead, Design = CastValue(list[dict[str, object]], CaseValue["readback"])
    assert FullRead["brep"] is True and Design["brep"] is False
    assert FullRead["counts"] == Design["counts"] == [1, 1, 11, 24, 16]
    assert (
        FullRead["drivers"]
        == Design["drivers"]
        == [
            "sldprt:parameter:19:D1",
            "sldprt:parameter:26:D1",
        ]
    )
    assert FullRead["values"] == Design["values"]
    assert FullRead["root_count"] == Design["root_count"] == 20
    assert CaseValue["streams"] == 10
    assert CaseValue["strict_refusal_runs"] == 16
    assert CaseValue["permissive_refusal_runs"] == 8
    assert CaseValue["runtime_data_reads"] == CaseValue["native_process_launches"] == 0
    assert Report["published_native_outputs"] == Report["heldout_credit"] == 0
