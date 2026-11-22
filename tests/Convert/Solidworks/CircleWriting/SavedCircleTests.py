from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import KMeasureRoot


# two native saves exercise strict dimensions and physical body ownership in fresh processes
def TestSavedCircle(TmpPath: FilePath) -> None:
    Command = KMeasureRoot / "re/tooling/sw2026/CheckSavedCircleRead.py"
    ReportPath = TmpPath / "SavedCircle.json"
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(Command),
            "--fixtures",
            "--output",
            str(ReportPath),
        ),
        capture_output=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(ReportPath.read_text("utf-8")))
    assert ReportValue["fresh_processes"] == 2
    assert ReportValue["linked_streams_exact"] == 6
    FirstValue, EditedValue = CastValue(list[dict[str, object]], ReportValue["cases"])
    assert FirstValue["phase"] == "open-save"
    assert EditedValue["phase"] == "edited-fresh-reopen"
    Refusals = CastValue(dict[str, object], EditedValue["refusals"])
    assert Refusals["unverified_geometry_unlinked"] is True
    assert Refusals["wrong_physical_atom"] == {
        "claimed": 102,
        "physical": 101,
        "refusal": "saved circle partition shell disagrees with the live body atom",
    }
