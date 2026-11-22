import json as JsonLib
from pathlib import Path as FilePath

from tests.Policy.ShardPlanTests import KRootPath, PlanSample, RunCommand


# runtime budgets must change real suite allocation without dropping coverage or exceeding the runner budget
def CheckBudgetFlow(TmpPath: FilePath) -> None:
    PlanPath, TestIds = PlanSample(TmpPath)
    HistoryPath = TmpPath / "History.json"
    _ = HistoryPath.write_text(
        JsonLib.dumps({"Durations": dict.fromkeys(TestIds, 10.0)})
    )
    PlanArgs = ["-m", "tools.TestShards.PlanShards", "--max-tests", "3"]
    PlanArgs += [
        "--collected",
        str(TmpPath / "Collected.txt"),
        "--history",
        str(HistoryPath),
    ]
    PlanArgs += [
        "--target-seconds",
        "10",
        "--runtime-shards",
        "4",
        "--output",
        str(PlanPath),
    ]
    Planned = RunCommand(PlanArgs, KRootPath)
    assert Planned.returncode == 0, Planned.stderr
    Plans = JsonLib.loads(PlanPath.read_text())["Shards"]
    assert len(Plans) == 4
    assert all(len(Shard["TestIds"]) <= 3 for Shard in Plans)
    assert sorted(TestId for Shard in Plans for TestId in Shard["TestIds"]) == sorted(
        TestIds
    )
    for Shard in Plans:
        SelectPath = TmpPath / "Selected.txt"
        _ = SelectPath.write_text("\n".join(Shard["TestIds"]) + "\n")
        ReportPath = TmpPath / "Reports" / str(Shard["Index"]) / "ShardReport.jsonl"
        Outcome = RunCommand(
            ["-m", "pytest", f"--report-log={ReportPath}", f"@{SelectPath}"], TmpPath
        )
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    MergeArgs = ["-m", "tools.TestShards.MergeReports", "--plan", str(PlanPath)]
    MergeArgs += [
        "--reports",
        str(TmpPath / "Reports"),
        "--output",
        str(TmpPath / "Durations.json"),
    ]
    Merged = RunCommand(MergeArgs, KRootPath)
    assert Merged.returncode == 0, Merged.stdout + Merged.stderr
