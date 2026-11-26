from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Policy.ShardPlanTests import KRootPath, PlanSample, RunCommand


# invalid runtime budgets must reject the real command without replacing an existing verified plan
@TestMark.parametrize(
    "BudgetArgs",
    (
        ("--target-seconds", "nan"),
        ("--target-seconds", "-1"),
        ("--runtime-shards", "0"),
    ),
)
def CheckBadBudget(TmpPath: FilePath, BudgetArgs: tuple[str, str]) -> None:
    PlanPath, _ = PlanSample(TmpPath)
    PriorBytes = PlanPath.read_bytes()
    PlanArgs = ["-m", "tools.TestShards.PlanShards", *BudgetArgs]
    PlanArgs += [
        "--collected",
        str(TmpPath / "Collected.txt"),
        "--output",
        str(PlanPath),
    ]
    Rejected = RunCommand(PlanArgs, KRootPath)
    assert Rejected.returncode == 2, Rejected.stdout + Rejected.stderr
    assert "runtime input error" in Rejected.stderr
    assert PlanPath.read_bytes() == PriorBytes
