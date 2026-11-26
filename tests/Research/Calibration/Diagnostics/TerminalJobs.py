from pathlib import Path as FilePath

from tests.Research.Calibration.Diagnostics.CalJsonTypes import (
    IsJsonItems,
    IsJsonRecord,
)
from tests.Research.Calibration.Diagnostics.ReadEvidence import ReadEvidence


# report attempt dispositions without releasing job identifiers or worker process identities
def TerminalJobs(TrialPath: FilePath) -> list[dict[str, object]]:
    Report = ReadEvidence(TrialPath / "Trial.json")
    JobsInfo = Report.get("jobs")
    if not IsJsonItems(JobsInfo):
        return []
    return [
        {
            Field: JobInfo.get(Field)
            for Field in ("state", "attempts", "exit_status", "signal", "stop_reason")
        }
        for JobInfo in JobsInfo
        if IsJsonRecord(JobInfo)
        and JobInfo.get("attempts")
        and JobInfo.get("state") != "completed"
    ][:8]
