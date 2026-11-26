from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# historical native receipts must retain exact public bindings while encoder research prepares unmeasured candidates
def TestPublicGate() -> None:
    RootPath = FilePath(__file__).resolve().parents[3]
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(RootPath / "re/solidworks/EncoderBoundary/CheckPublication.py"),
            "--root",
            str(RootPath),
        ),
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["passed"] is True
    assert (
        ReportValue["native_launches"] == ReportValue["runtime_external_accesses"] == 0
    )
    assert ReportValue["evidence_scope"] == "historical_receipt_replay_only"
    CaseRows = CastValue(list[dict[str, object]], ReportValue["results"])
    assert {CaseValue["role"] for CaseValue in CaseRows} == {"Skew", "Step"}
    for CaseValue in CaseRows:
        assert CaseValue["accepted_streams"] == 2
        assert set(CastValue(list[str], CaseValue["refusals"])) == {
            "missing_receipt",
            "changed_model",
            "different_epoch",
            "different_locator",
            "bad_build",
            "missing_reopen",
            "failed_control",
        }
