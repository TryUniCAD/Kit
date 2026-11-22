import json as JsonCodec
from pathlib import Path as FilePath


# failed sweeps need the stopped trial and sanitized failure operation in remote process logs
def TrialDetails(ReportPath: FilePath) -> str:
    try:
        Report = JsonCodec.loads(ReportPath.read_text(encoding="utf-8"))
        if "supervision_error" in Report:
            return (
                "\nSupervision error: "
                + JsonCodec.dumps(Report["supervision_error"])[:2048]
            )
        Details = [
            {
                KeyName: Trial[KeyName]
                for KeyName in (
                    "requested_concurrency",
                    "completed_jobs",
                    "expected_jobs",
                    "wall_seconds",
                    "incomplete_reasons",
                )
            }
            | {"supervision_error": Trial.get("supervision_error")}
            for Trial in Report["trials"]
        ]
    except (OSError, ValueError, KeyError, TypeError):
        return ""
    return "\nTrial details: " + JsonCodec.dumps(Details)[:2048]
