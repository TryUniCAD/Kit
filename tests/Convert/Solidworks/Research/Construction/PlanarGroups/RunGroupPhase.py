from pathlib import Path
from typing import cast as CastValue
import json
import subprocess
import sys


# complete group tests must cross the real isolated interpreter and stdin generation boundary with native files and cad imports unavailable to the writer
def RunGroupPhase(RequestValue: dict[str, object]) -> dict[str, object]:
    RootValue = Path(__file__).resolve().parents[6]
    ResultValue = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            str(RootValue / "re/tooling/sw2026/SdkPlanarGroupProcess.py"),
            str(RootValue),
        ],
        input=json.dumps(RequestValue, allow_nan=False),
        text=True,
        capture_output=True,
        timeout=120,
        check=True,
    )
    ReportValue = CastValue(dict[str, object], json.loads(ResultValue.stdout))
    assert ReportValue["passed"] is True
    assert ReportValue["runtime_input_file_reads"] == 0
    assert ReportValue["sdk_runtime_research_imports"] == 0
    assert ReportValue["native_acceptance"] is False
    assert ReportValue["heldout_inputs_read"] == 0
    return ReportValue
