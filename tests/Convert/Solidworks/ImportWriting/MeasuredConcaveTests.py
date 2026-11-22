from json import loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Api.ApiTestPaths import KRootPath


# the complete suite exercises attributed concave publication in a fresh sdk process
def TestConcave() -> None:
    ScriptPath = (
        KRootPath / "re/tooling/sw2026/imported_body_source/VerifyMeasuredConcave.py"
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
    assert ReportValue["rejected_paths_preserved"] is True
    Readback = ReportValue["readback"]
    assert Readback["topology"] == [1, 1, 8, 18, 12]
    assert Readback["volume_mm3"] == 5160.0
    assert len(Readback["body_attributes"]) == 5
    if "unmatched_compressor" in ReportValue:
        assert ReportValue["exact_publications"] == 0
        assert "zlib-ng" in ReportValue["unmatched_compressor"]
    else:
        assert ReportValue["exact_publications"] == 2
        assert ReportValue["exact_streams"] == 12
        assert len(ReportValue["refusals"]) == 10
