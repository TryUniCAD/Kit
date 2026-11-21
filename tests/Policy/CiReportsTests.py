import os as SystemEnv
import subprocess as Subprocess
import tempfile as Tempfile
from pathlib import Path as FilePath

import pytest as Pytest


# the report flow contract needs boundary coverage so the real command boundary enforces repository contracts
@Pytest.mark.parametrize(
    "CaseMode,CheckName",
    (
        ("status", "Ruff"),
        ("external", "Ruff"),
        ("unlisted-job", "Unlisted job"),
        ("unlisted-run", "Unlisted workflow"),
        ("check", "Ruff"),
        ("check", "Pyright"),
        ("check", "Mypy"),
        ("check", "Python steering"),
        ("check", "Research CLI compatibility"),
        ("check", "Research CLI Windows compatibility"),
        ("check", "Verify CI policy and pytest compatibility"),
        ("check", "Verify rationale comments on changed sources"),
        ("check", "Build and verify release artifacts"),
        ("check", "Label first-time contributors"),
        ("check", "Test suite / Plan"),
        ("check", "Test suite / Report"),
        ("quality-fork", "Ruff"),
        ("quality-docs", "Ruff"),
    ),
)
def CheckReportFlow(CaseMode: str, CheckName: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    ScriptPath = RootPath / "tests/Policy/CiAggregation/RunAggregate.cjs"
    ExpectedPass = CaseMode != "check"
    with Tempfile.TemporaryDirectory() as TempPath:
        ResultInfo = Subprocess.run(
            ["node", str(ScriptPath), CaseMode, "failure", CheckName],
            cwd=TempPath,
            env={
                **SystemEnv.environ,
                "RUNNER_TEMP": str(FilePath(TempPath) / "OtherTemp"),
            },
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        assert not (FilePath(TempPath) / "OtherTemp").exists()
        EvidencePath = FilePath(TempPath) / "PrCiEvidence/Evidence.json"
        assert EvidencePath.exists() == (
            ExpectedPass and not CaseMode.startswith("queue")
        ), ResultInfo.stderr
    assert ResultInfo.returncode == (0 if ExpectedPass else 1)
    assert "Review report" not in ResultInfo.stdout
    assert "Unlisted job" not in ResultInfo.stdout
    assert "Unlisted workflow" not in ResultInfo.stdout
    if ExpectedPass:
        assert "CI passed" in ResultInfo.stdout
        assert "Ruff" in ResultInfo.stdout
    else:
        assert f"CI failed: {CheckName}" in ResultInfo.stderr


# skipped shared checks must block enrollment while a deferred integration check may wait
@Pytest.mark.parametrize(
    "CheckName,ExitCode",
    (
        ("Pyright", 1),
        ("Mypy", 1),
        ("Python steering", 1),
        ("Research CLI compatibility", 0),
    ),
)
def CheckPhaseSkip(CheckName: str, ExitCode: int, TmpPath: FilePath) -> None:
    ScriptPath = (
        FilePath(__file__).resolve().parents[2]
        / "tests/Policy/CiAggregation/RunAggregate.cjs"
    )
    Result = Subprocess.run(
        ["node", str(ScriptPath), "check", "skipped", CheckName],
        cwd=TmpPath,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert Result.returncode == ExitCode, Result.stderr


# process execution verifies trusted base phase selection and rejects unreadable markers
@Pytest.mark.parametrize(
    "CaseMode,PhaseName,ExitCode",
    (
        ("pull", "pull_request", 0),
        ("queue", "merge_group", 0),
        ("legacy", "legacy", 0),
        ("invalid", "", 1),
        ("denied", "", 1),
    ),
)
def TestPhaseModes(CaseMode: str, PhaseName: str, ExitCode: int) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    ScriptPath = RootPath / "tests/Policy/CiAggregation/RunPhase.cjs"
    ResultInfo = Subprocess.run(
        ["node", str(ScriptPath), CaseMode],
        cwd=RootPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert ResultInfo.returncode == ExitCode, ResultInfo.stderr
    if ExitCode == 0:
        assert f"phase={PhaseName}" in ResultInfo.stdout
    else:
        assert "phase=" not in ResultInfo.stdout
