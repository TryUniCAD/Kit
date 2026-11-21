import json as JsonCodec
import sys as System
from errno import EACCES as AccessDenied
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.Windows.Calibration.RunCalError import RunCalError
from tests.Research.Windows.WaitForExit import WaitForExit


# a refused observation must preserve its native codes without exposing private exception text or leaving claims
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
@Pytest.mark.parametrize("CleanupFails", (False, True))
def CheckCalError(TmpPath: FilePath, CleanupFails: bool) -> None:
    Expected: dict[str, str | int] = {
        "stage": "sample_worker_memory",
        "error_type": "PermissionError",
        "errno": AccessDenied,
        "winerror": 5,
    }
    OutputPath = RunCalError(TmpPath, CleanupFails, Expected)
    RawReport = (OutputPath / "Calibration.json").read_text(encoding="utf-8")
    Report = JsonCodec.loads(RawReport)
    assert (
        Report["completed_sweep"] is False and Report["recommended_concurrency"] is None
    )
    assert "fixture-private-" not in RawReport
    TrialPath = OutputPath / "Trial1"
    Launcher = JsonCodec.loads(
        (TrialPath / "SupervisorProcess.json").read_text(encoding="utf-8")
    )
    WaitForExit(Launcher["pid"])
    assert not (OutputPath / "Trial2").exists()
    if CleanupFails:
        assert Report["stop_reason"] == "calibration_error"
        assert Report["error"] == "OSError: fixture settlement fault"
        assert Report["cleanup_verified"] is False
        assert Report["supervision_error"] == Expected
        assert not (TrialPath / "Trial.json").exists()
        return
    (Trial,) = Report["trials"]
    assert Trial["supervision_error"] == Expected
    assert Report["stop_reason"] == "measurement_or_supervision_error:PermissionError"
    SavedTrial = JsonCodec.loads((TrialPath / "Trial.json").read_text(encoding="utf-8"))
    assert SavedTrial["supervision_error"] == Expected
    Cleanup = JsonCodec.loads((TrialPath / "Cleanup.json").read_text(encoding="utf-8"))
    assert Cleanup["claims_empty"] is True and Cleanup["sessions_empty"] is True
    assert Cleanup["job_members_empty"] is True
