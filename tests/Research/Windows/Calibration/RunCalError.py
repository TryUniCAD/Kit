import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.Calibration.BuildManifest import BuildManifest
from tests.Research.Calibration.ReadCalRun import ReadCalRun
from tests.Research.Calibration.RunCalibration import KRepoRoot
from tests.Research.Windows.Calibration.CheckDecStop import CheckDecStop

# the process fixture supplies a reproducible windows error without depending on a sharing race
KFaultScript = """
import sys

sys.path.insert(0, sys.argv.pop(1))
import Calibration

settle = Calibration.settle_supervisor

def fail_sample(process, directory):
    raise OSError(0, "fixture-private-message", "fixture-private-path", 5)

def fail_after_settlement(process, identity, stopping):
    settle(process, identity, stopping)
    raise OSError("fixture settlement fault")

Calibration.sample_workers = fail_sample
if sys.argv.pop(1) == "fail-settlement":
    Calibration.settle_supervisor = fail_after_settlement
raise SystemExit(Calibration.main())
"""


# execution must pass through calibration and its real supervisor before inspecting a failure report
def RunCalError(
    RootPath: FilePath, CleanupFails: bool, Expected: dict[str, str | int]
) -> FilePath:
    ManifestPath = BuildManifest(RootPath)
    OutputPath = RootPath / "DeniedSample"
    Process = Subprocess.run(
        [
            System.executable,
            "-I",
            "-B",
            "-c",
            KFaultScript,
            str(KRepoRoot / "re/automation"),
            "fail-settlement" if CleanupFails else "settle",
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
    Report = ReadCalRun(Process, 1 if CleanupFails else 2, OutputPath)
    with Pytest.raises(AssertionError) as Mismatch:
        _ = ReadCalRun(Process, 2 if CleanupFails else 0, OutputPath)
    Prefix = "\nSupervision error: " if CleanupFails else '"supervision_error": '
    Detail = JsonCodec.dumps(Expected, sort_keys=True)
    assert Prefix + Detail in str(Mismatch.value)
    assert "fixture-private-" not in Process.stdout + Process.stderr
    assert "fixture-private-" not in str(Mismatch.value)
    if not CleanupFails:
        with Pytest.raises(AssertionError) as StopMismatch:
            CheckDecStop(Report, OutputPath)
        assert Prefix + Detail in str(StopMismatch.value)
    return OutputPath
