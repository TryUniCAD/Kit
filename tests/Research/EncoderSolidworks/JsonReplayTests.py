from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# prepared constructor json must replay without a native source or renewed source admission in another process
def TestJsonReplay() -> None:
    RootPath = FilePath(__file__).resolve().parents[3]
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(RootPath / "re/solidworks/EncoderBoundary/CheckJsonReplay.py"),
            "--root",
            str(RootPath),
        ),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["passed"] is True
    assert ReportValue["fresh_processes"] == 4
    assert (
        ReportValue["native_launches"]
        == ReportValue["native_source_files_written"]
        == 0
    )
    CaseRows = CastValue(list[dict[str, object]], ReportValue["results"])
    assert {CaseValue["role"] for CaseValue in CaseRows} == {
        "BaselineReconstruction",
        "BaselineEdited",
        "HeldOutReconstruction",
        "HeldOutEdited",
    }
    for CaseValue in CaseRows:
        assert (
            CaseValue["external_access_attempts"]
            == CaseValue["source_admission_calls"]
            == 0
        )
        assert set(CastValue(list[str], CaseValue["refusals"])) == {
            "inconsistent_depth",
            "extra_metadata",
        }
        assert (
            CaseValue["case_variant_locator"]
            == CaseValue["case_variant_header_locator"]
        )
        assert CastValue(str, CaseValue["case_variant_locator"]).endswith(
            ("EDITED.SLDPRT", "RECONSTRUCTION.SLDPRT")
        )
        assert CaseValue["case_variant_sha256"] != CaseValue["sha256"]
        if ReportValue["exact_measured_runtime"] is True:
            assert CaseValue["measured_match"] is True
