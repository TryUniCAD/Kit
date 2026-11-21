import subprocess as Subprocess
from pathlib import Path as FilePath

from tests.Research.Calibration.Diagnostics.TrialDetails import TrialDetails
from tests.Research.Calibration.Diagnostics.TrialFailures import TrialFailures
from tests.Research.Calibration.Diagnostics.TrialMarkers import TrialMarkers


# an abruptly stopped interpreter can return an operating system status without output
def FailureDetails(
    Process: Subprocess.CompletedProcess[str], ExitCode: int, ReportPath: FilePath
) -> str:
    Actual = Process.returncode
    OutputPath = ReportPath.parent
    return (
        f"Calibration {OutputPath.name} exited {Actual} (0x{Actual & 0xFFFFFFFF:08X}) "
        + f"instead of {ExitCode}; {ReportPath.name} present: {ReportPath.is_file()}"
        + TrialMarkers(OutputPath)
        + TrialDetails(ReportPath)
        + TrialFailures(OutputPath)
        + f"\nCaptured stderr tail: {Process.stderr[-4096:]!r}"
        + f"\nCaptured stdout tail: {Process.stdout[-2048:]!r}"
    )
