import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from tests.Research.Calibration.ReadCalRun import ReadCalRun

# the subprocess must use the checked in calibration entry point regardless of the caller directory
KRepoRoot = FilePath(__file__).resolve().parents[3]


# calibration checks must verify the actual command exit and durable report together
def RunCalibration(
    ManifestPath: FilePath,
    OutputPath: FilePath,
    ExitCode: int | None = 0,
    MaxWorkers: int | None = None,
    CompareGrouped: bool = False,
    TimeoutSeconds: int = 240,
) -> dict[str, object]:
    ModeItems = ["--compare-grouped"] if CompareGrouped else []
    if MaxWorkers is not None:
        ModeItems.extend(("--max-concurrency", str(MaxWorkers)))
    Process = Subprocess.run(
        [
            System.executable,
            "-X",
            "faulthandler",
            str(KRepoRoot / "re/automation/Calibration.py"),
            "--manifest",
            str(ManifestPath),
            "--output",
            str(OutputPath),
        ]
        + ModeItems,
        capture_output=True,
        text=True,
        check=False,
        timeout=TimeoutSeconds,
    )
    return ReadCalRun(Process, ExitCode, OutputPath)
