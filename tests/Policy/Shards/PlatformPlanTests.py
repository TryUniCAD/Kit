import json as JsonLib
from os import environ as KEnvironment
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from pytest import mark as TestMark

from tests.Policy.ShardPlanTests import KRootPath, PlanSample
from tests.Policy.Shards.FindTestShell import FindTestShell
from tests.Policy.Shards.RunNativeShard import RunNativeShard


# scheduling changes must retain actual pytest outcomes through the complete native reporting boundary
@TestMark.parametrize("HasHistory", (False, True))
@TestMark.parametrize("ShardCount", (4, 5))
def CheckNativeFlow(TmpPath: FilePath, HasHistory: bool, ShardCount: int) -> None:
    _, CollectedIds = PlanSample(TmpPath)
    TestIds = sorted(CollectedIds)
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
    for ShardIndex in range(ShardCount):
        ReportRoot = TmpPath / f"Platform-shard-{ShardIndex + 1}-1"
        ReportRoot.mkdir()
        RunNativeShard(
            TmpPath,
            ReportRoot,
            TestIds,
            HistoryPath,
            ShardIndex,
            ShardCount,
            HasHistory,
        )
    DurationPath = TmpPath / "Durations.json"
    Reported = RunProcess(
        [
            FindTestShell(),
            (KRootPath / ".github/scripts/VerifyShardReports.sh").as_posix(),
            TmpPath.as_posix(),
            "Platform",
            "1",
            "^test_sample.py::",
            DurationPath.as_posix(),
            str(ShardCount),
        ],
        env={
            **KEnvironment,
            "GITHUB_STEP_SUMMARY": (TmpPath / "Summary.md").as_posix(),
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Reported.returncode == 0, Reported.stdout + Reported.stderr
    Durations = JsonLib.loads(DurationPath.read_text())["Durations"]
    assert sorted(Durations) == sorted(TestIds)
    assert all(Seconds >= 0 for Seconds in Durations.values())
