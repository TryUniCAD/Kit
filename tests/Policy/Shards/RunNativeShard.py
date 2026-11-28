from pathlib import Path as FilePath

from tests.Policy.ShardPlanTests import KRootPath, RunCommand


# native scheduling evidence requires each selected roster to execute through the real pytest process
def RunNativeShard(
    TmpPath: FilePath,
    ReportRoot: FilePath,
    TestIds: list[str],
    HistoryPath: FilePath,
    ShardIndex: int,
    ShardCount: int,
    HasHistory: bool,
) -> None:
    CollectedPath = ReportRoot / "Collected.txt"
    _ = CollectedPath.write_text("\n".join(TestIds) + "\n", newline="\n")
    SelectArgs = ["-m", "tools.TestShards.Platform.SelectShard"]
    SelectArgs += ["--collected", str(CollectedPath), "--history", str(HistoryPath)]
    SelectArgs += ["--index", str(ShardIndex), "--count", str(ShardCount)]
    SelectArgs += ["--output", str(ReportRoot / "Selected.txt")]
    Selected = RunCommand(SelectArgs, KRootPath)
    assert Selected.returncode == 0, Selected.stderr
    assert b"\r" not in (ReportRoot / "Selected.txt").read_bytes()
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
