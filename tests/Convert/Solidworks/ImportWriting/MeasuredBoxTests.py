from json import loads as LoadJson
from os import name as OsName
from subprocess import run as RunProcess
from sys import executable as PythonExec

from pytest import mark as MarkCase

from tests.Convert.Api.ApiTestPaths import KRootPath
from tests.Convert.Solidworks.ImportWriting.CheckImportPath import CheckImportPath


# the complete suite must exercise the measured geometry and refusal boundary in isolation
def TestMeasuredBox() -> None:
    ScriptPath = (
        KRootPath / "re/tooling/sw2026/imported_body_source/VerifyMeasuredBox.py"
    )
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(ScriptPath), "--remote-coverage"),
        capture_output=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = LoadJson(Outcome.stdout)
    assert ReportValue["passed"] is True
    assert ReportValue["runtime_external_events"] == 0
    assert ReportValue["readback"]["topology"] == [1, 1, 6, 12, 8]
    assert ReportValue["readback"]["volume_mm3"] == 2574.0
    if "unmatched_compressor" in ReportValue:
        assert ReportValue["exact_publications"] == 0
        assert "zlib-ng" in ReportValue["unmatched_compressor"]
        assert ReportValue["distinct_compression_refused"] == dict.fromkeys(
            ("direct", "registry"), "no exact native measurement"
        )
    else:
        assert ReportValue["exact_publications"] == 2
        assert ReportValue["exact_streams"] == 12
        assert len(ReportValue["refusals"]) == 11


# the real windows path hands the measured locator through registry staging and direct writing
@MarkCase.skipif(
    OsName != "nt", reason="the measured physical locator requires Windows"
)
def TestBoxWinPath() -> None:
    CheckImportPath("RectangularBare", 9914)
