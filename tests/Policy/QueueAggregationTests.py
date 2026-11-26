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
        "Test suite / Platform (windows-2025) / shard-5",
        "Test suite / Platform (macos-26)",
        "Test suite / Platform (macos-26) / shard-1",
        "Test suite / Platform (macos-26) / shard-2",
        "Test suite / Platform (macos-26) / shard-3",
        "Test suite / Platform (macos-26) / shard-4",
        "Test suite / Platform (macos-26) / shard-5",
        "Pyright",
        "Mypy",
        "Python steering",
        "Research CLI Windows compatibility",
        "Research CLI Windows compatibility / shard-1",
        "Research CLI Windows compatibility / shard-2",
        "Research CLI Windows compatibility / shard-3",
        "Research CLI Windows compatibility / shard-4",
        "Verify CI policy and pytest compatibility",
        "Native file compatibility",
        "Native file compatibility / shard-1",
        "Native file compatibility / shard-2",
        "Native file compatibility / shard-3",
        "Native file compatibility / shard-4",
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
    OptionalShard = CheckName.endswith(" / shard-5")
    Passed = Verdict == "success" or (
        OptionalShard and CaseMode == "queue" and Verdict == "skipped"
    )
    with Tempfile.TemporaryDirectory() as TempPath:
        ResultInfo = Subprocess.run(
            [
                "node",
                str(ScriptPath),
                CaseMode,
                Verdict,
                CheckName,
                "5" if OptionalShard else "4",
            ],
            cwd=TempPath,
            env={**SystemEnv.environ, "RUNNER_TEMP": TempPath},
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        assert not (FilePath(TempPath) / "PrCiEvidence/Evidence.json").exists()
    assert ResultInfo.returncode == (0 if Passed else 1), ResultInfo.stderr
    assert ("CI passed" in ResultInfo.stdout) == Passed
    if not Passed:
        assert "CI failed" in ResultInfo.stderr


# queue aggregation polling must pace itself within the shared token budget and treat rate limits as waits
@Pytest.mark.parametrize(
    "CaseName, Passed, Expected",
    (
        (
            "plain",
            True,
            ("next poll in 720 s", "next poll in 576 s", "next poll in 231 s"),
        ),
        ("ratelimit", True, ("GitHub API rate limit reached; retrying in 601 s",)),
        ("secondary", True, ("GitHub API rate limit reached; retrying in 60 s",)),
        ("forbidden", False, ("Resource not accessible by integration",)),
        ("pacing", True, ("600/1000 remaining; next poll in 3600 s",)),
        ("exhausted", True, ("450/1000 remaining; next poll in 3601 s",)),
        ("failure", False, ("CI failed: Merge queue",)),
    ),
)
def CheckPolling(CaseName: str, Passed: bool, Expected: tuple[str, ...]) -> None:
    ScriptPath = (
        FilePath(__file__).resolve().parents[2]
        / "tests/Policy/CiAggregation/RunPolling.cjs"
    )
    ResultInfo = Subprocess.run(
        ["node", str(ScriptPath), CaseName],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    Output = ResultInfo.stdout + ResultInfo.stderr
    assert ResultInfo.returncode == (0 if Passed else 1), Output
    assert ("CI passed" in ResultInfo.stdout) == Passed
    assert "No candidate workflow has finished since the last read" in Output
    for Snippet in Expected:
        assert Snippet in Output, Output
