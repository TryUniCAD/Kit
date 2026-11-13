from __future__ import annotations

import os as OsLib

from WriteOutputs import KOutputPath


def AppendSummary() -> None:
    SummaryName = OsLib.environ.get("GITHUB_STEP_SUMMARY")
    ReportPath = KOutputPath / "Report.md"
    if not SummaryName or not ReportPath.is_file():
        return
    with open(SummaryName, "a", encoding="utf-8") as SummaryFile:
        _ = SummaryFile.write(ReportPath.read_text(encoding="utf-8"))
