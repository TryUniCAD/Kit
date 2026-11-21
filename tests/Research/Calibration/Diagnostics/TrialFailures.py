import json as JsonCodec
from pathlib import Path as FilePath

from tests.Research.Calibration.Diagnostics.TerminalEvents import TerminalEvents
from tests.Research.Calibration.Diagnostics.TerminalJobs import TerminalJobs


# fixed trial names keep process diagnostics within the private fixture directory
def TrialFailures(OutputPath: FilePath) -> str:
    Details: dict[str, object] = {}
    for NameText in (
        "Trial1",
        "Trial2",
        "Trial4",
        "Trial8",
        "Trial16",
        "Singleton",
        "Grouped",
    ):
        TrialPath = OutputPath / NameText
        JobsInfo = TerminalJobs(TrialPath)
        Events = TerminalEvents(TrialPath)
        if JobsInfo or Events:
            Details[TrialPath.name] = {"jobs": JobsInfo, "events": Events}
    return "\nTrial terminal evidence: " + JsonCodec.dumps(Details)[:4096]
