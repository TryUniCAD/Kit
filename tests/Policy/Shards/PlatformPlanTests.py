import json as JsonLib
from os import environ as KEnvironment
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from pytest import mark as TestMark

from tests.Policy.ShardPlanTests import KRootPath, PlanSample, RunCommand


# scheduling changes must retain actual pytest outcomes through the complete native reporting boundary
@TestMark.parametrize("HasHistory", (False, True))
def CheckNativeFlow(TmpPath: FilePath, HasHistory: bool) -> None:
    _, TestIds = PlanSample(TmpPath)
    HistoryPath = TmpPath / "History.json"
    if HasHistory:
        _ = HistoryPath.write_text(
            JsonLib.dumps(
                {
                    "Durations": {
                        **dict.fromkeys(TestIds, 1.0),
                        TestIds[0]: 100.0,
                        TestIds[4]: 100.0,
                    }
                }
            )
        )
    for ShardIndex in range(4):
        ReportRoot = TmpPath / f"Platform-shard-{ShardIndex + 1}-1"
        ReportRoot.mkdir()
        CollectedPath = ReportRoot / "Collected.txt"
        _ = CollectedPath.write_text("\n".join(TestIds) + "\n")
        SelectArgs = ["-m", "tools.TestShards.Platform.SelectShard"]
        SelectArgs += ["--collected", str(CollectedPath), "--history", str(HistoryPath)]
        SelectArgs += ["--index", str(ShardIndex), "--count", "4"]
        SelectArgs += ["--output", str(ReportRoot / "Selected.txt")]
        Selected = RunCommand(SelectArgs, KRootPath)
        assert Selected.returncode == 0, Selected.stderr
        if HasHistory:
            SelectedIds = (ReportRoot / "Selected.txt").read_text().splitlines()
            assert not (TestIds[0] in SelectedIds and TestIds[4] in SelectedIds)
        Outcome = RunCommand(
            [
                "-m",
                "pytest",
                f"--report-log={ReportRoot / 'Report.jsonl'}",
                f"@{ReportRoot / 'Selected.txt'}",
            ],
            TmpPath,
        )
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    SummaryPath = TmpPath / "Summary.md"
    DurationPath = TmpPath / "Durations.json"
    Reported = RunProcess(
        [
            "bash",
            str(KRootPath / ".github/scripts/VerifyShardReports.sh"),
            str(TmpPath),
            "Platform",
            "1",
            "^test_sample.py::",
            str(DurationPath),
        ],
        env={**KEnvironment, "GITHUB_STEP_SUMMARY": str(SummaryPath)},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Reported.returncode == 0, Reported.stdout + Reported.stderr
    Durations = JsonLib.loads(DurationPath.read_text())["Durations"]
    assert sorted(Durations) == sorted(TestIds)
    assert all(Seconds >= 0 for Seconds in Durations.values())
