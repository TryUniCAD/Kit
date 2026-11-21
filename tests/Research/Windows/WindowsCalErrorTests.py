import json as JsonCodec
import subprocess as Subprocess
import sys as System
from errno import EACCES as AccessDenied
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.Calibration.BuildManifest import BuildManifest
from tests.Research.Calibration.RunCalibration import KRepoRoot, TrialDetails

# the process fixture supplies a reproducible windows error without depending on a sharing race
KFaultScript = """
import sys

sys.path.insert(0, sys.argv.pop(1))
import Calibration

def fail_sample(process, directory):
    raise OSError(0, "fixture-private-message", "fixture-private-path", 5)

Calibration.sample_workers = fail_sample
raise SystemExit(Calibration.main())
"""


# a refused observation must preserve its native codes without exposing private exception text or leaving claims
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckCalError(TmpPath: FilePath) -> None:
    ManifestPath = BuildManifest(TmpPath)
    OutputPath = TmpPath / "DeniedSample"
    Process = Subprocess.run(
        [
            System.executable,
            "-I",
            "-B",
            "-c",
            KFaultScript,
            str(KRepoRoot / "re/automation"),
            "--manifest",
            str(ManifestPath),
            "--output",
            str(OutputPath),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Process.returncode == 2, (Process.stdout, Process.stderr)
    ReportPath = OutputPath / "Calibration.json"
    RawReport = ReportPath.read_text(encoding="utf-8")
    Report = JsonCodec.loads(RawReport)
    (Trial,) = Report["trials"]
    Expected = {
        "stage": "sample_worker_memory",
        "error_type": "PermissionError",
        "errno": AccessDenied,
        "winerror": 5,
    }
    assert Trial["supervision_error"] == Expected
    assert Report["stop_reason"] == "measurement_or_supervision_error:PermissionError"
    assert (
        Report["completed_sweep"] is False and Report["recommended_concurrency"] is None
    )
    assert JsonCodec.dumps(Expected, sort_keys=True) in TrialDetails(ReportPath)
    assert "fixture-private-" not in RawReport + Process.stdout + Process.stderr
    TrialPath = OutputPath / "Trial1"
    SavedTrial = JsonCodec.loads((TrialPath / "Trial.json").read_text(encoding="utf-8"))
    assert SavedTrial["supervision_error"] == Expected
    Cleanup = JsonCodec.loads((TrialPath / "Cleanup.json").read_text(encoding="utf-8"))
    assert Cleanup["claims_empty"] is True and Cleanup["sessions_empty"] is True
    assert Cleanup["job_members_empty"] is True and not (OutputPath / "Trial2").exists()
