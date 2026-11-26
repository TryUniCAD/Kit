import json as JsonCodec
import subprocess as Subprocess
from pathlib import Path as FilePath

from tests.Research.Calibration.Diagnostics.FailureDetails import FailureDetails
from tests.Research.Calibration.Diagnostics.ReadEvidence import ReadEvidence


# hosted calibration checks must verify the real exit and show saved evidence on a mismatch
def ReadCalRun(
    Process: Subprocess.CompletedProcess[str],
    ExitCode: int | None,
    OutputPath: FilePath,
) -> dict[str, object]:
    ReportPath = OutputPath / "Calibration.json"
    Expected = ExitCode
    if Expected is None:
        Expected = 0 if ReadEvidence(ReportPath).get("completed_sweep") is True else 2
    assert Process.returncode == Expected, FailureDetails(Process, Expected, ReportPath)
    Report: dict[str, object] = JsonCodec.loads(ReportPath.read_text(encoding="utf-8"))
    return Report
