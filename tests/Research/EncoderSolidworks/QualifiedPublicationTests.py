from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# fresh native receipts must bind the actual measured compression and executable at both public writer boundaries
def TestQualified() -> None:
    RootPath = FilePath(__file__).resolve().parents[3]
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(
                RootPath / "re/solidworks/EncoderBoundary/CheckQualifiedPublication.py"
            ),
            "--root",
            str(RootPath),
        ),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    CaseRows = CastValue(list[dict[str, object]], ReportValue["results"])
    assert {CaseValue["role"] for CaseValue in CaseRows} == {
        "BaselineReconstruction",
        "BaselineEdited",
        "HeldOutReconstruction",
        "HeldOutEdited",
    }
    for CaseValue in CaseRows:
        Accepted = CastValue(int, CaseValue["accepted"])
        assert Accepted in (0, 2)
        assert CaseValue["unknown_identity_refused"] == 2
        assert CaseValue["oversized_measurement_refused"] == 2 * Accepted
