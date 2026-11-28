import json as JsonTools
import subprocess as ProcessTools
import sys as SysTools
import tempfile as TempTools
from pathlib import Path

import pytest as Pytest


# the real validation process must reject malformed or stale reports before any publisher can consume them
@Pytest.mark.parametrize("CaseName", ("valid", "stale", "extra", "score", "location"))
def CheckReviewCli(CaseName: str) -> None:
    RootPath = Path(__file__).resolve().parents[2]
    Context: dict[str, object] = {
        "evidence": {"head_sha": "a" * 40, "base_sha": "b" * 40},
        "files": [{"path": "Source.py"}],
    }
    Report: dict[str, object] = {
        "head": "a" * 40,
        "base": "b" * 40,
        "complete": True,
        "scope_matches": True,
        "score": 4,
        "summary": "Source review only",
        "findings": [],
    }
    if CaseName == "stale":
        Report["head"] = "c" * 40
    if CaseName == "extra":
        Report["approve"] = True
    if CaseName == "score":
        Report["score"] = True
    if CaseName == "location":
        Report["findings"] = [
            {
                "priority": "P1",
                "path": "Other.py",
                "line": 1,
                "title": "Wrong source",
                "body": "Outside the reviewed change",
            }
        ]
    with TempTools.TemporaryDirectory() as TempName:
        TempPath = Path(TempName)
        assert (TempPath / "Context.json").write_text(JsonTools.dumps(Context)) > 0
        assert (TempPath / "Report.json").write_text(JsonTools.dumps(Report)) > 0
        Result = ProcessTools.run(
            [
                SysTools.executable,
                str(RootPath / ".github/scripts/Review/Validate.py"),
                str(TempPath / "Report.json"),
                str(TempPath / "Context.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    assert (Result.returncode == 0) == (CaseName == "valid"), Result.stderr
