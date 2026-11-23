import os as SystemEnv
import subprocess as Subprocess
import tempfile as Tempfile
from pathlib import Path as FilePath

import pytest as Pytest


# the queue gate contract needs boundary coverage so the real command boundary enforces repository contracts
@Pytest.mark.parametrize(
    "CheckName",
    (
        "Scorecard",
        "dlint",
        "Analyze python",
        "Run the complete test suite",
        "Test suite / Plan",
        "Test suite / Shard (2)",
        "Test suite / Report",
        "Test suite / Platform (windows-2025)",
        "Test suite / Platform (windows-2025) / shard-1",
        "Test suite / Platform (windows-2025) / shard-2",
        "Test suite / Platform (windows-2025) / shard-3",
        "Test suite / Platform (windows-2025) / shard-4",
        "Test suite / Platform (macos-26)",
        "Test suite / Platform (macos-26) / shard-1",
        "Test suite / Platform (macos-26) / shard-2",
        "Test suite / Platform (macos-26) / shard-3",
        "Test suite / Platform (macos-26) / shard-4",
        "Pyright",
        "Mypy",
        "Python steering",
        "Research CLI compatibility",
        "Research CLI Windows compatibility",
        "Research CLI Windows compatibility / shard-1",
        "Research CLI Windows compatibility / shard-2",
        "Research CLI Windows compatibility / shard-3",
        "Research CLI Windows compatibility / shard-4",
        "Verify CI policy and pytest compatibility",
        "Native file compatibility / solidworks",
        "Native file compatibility / parasolid",
        "Native file compatibility / rationale",
        "Analyze javascript-typescript",
        "Analyze java-kotlin",
    ),
)
@Pytest.mark.parametrize(
    "Verdict", ("success", "failure", "neutral", "skipped", "cancelled", "timed_out")
)
@Pytest.mark.parametrize("CaseMode", ("queue", "queue-run"))
def TestQueueGate(CheckName: str, Verdict: str, CaseMode: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    ScriptPath = RootPath / "tests/Policy/CiAggregation/RunAggregate.cjs"
    with Tempfile.TemporaryDirectory() as TempPath:
        ResultInfo = Subprocess.run(
            ["node", str(ScriptPath), CaseMode, Verdict, CheckName],
            cwd=TempPath,
            env={**SystemEnv.environ, "RUNNER_TEMP": TempPath},
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        assert not (FilePath(TempPath) / "PrCiEvidence/Evidence.json").exists()
    assert ResultInfo.returncode == (
        0 if Verdict == "success" else 1
    ), ResultInfo.stderr
    assert ("CI passed" in ResultInfo.stdout) == (Verdict == "success")
    if Verdict != "success":
        assert "CI failed" in ResultInfo.stderr
