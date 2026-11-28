from pathlib import Path

from tests.Policy.ContextBudget.GitCommand import GitCommand
from tests.Policy.ContextBudget.WriteBudgetFiles import WritePolicies, WriteSources


# commits and the independent target branch bind the process check to real merge base content
def MakeBudgetRepo(
    RootPath: Path, CaseName: str
) -> tuple[str, str, str, tuple[str, ...]]:
    RootPath.mkdir()
    InitData = GitCommand(RootPath, "init", "--initial-branch=main")
    assert "Initialized" in InitData
    ConfigData = GitCommand(RootPath, "config", "user.name", "Context Fixture")
    assert not ConfigData
    ConfigData = GitCommand(RootPath, "config", "user.email", "context@example.invalid")
    assert not ConfigData
    WritePolicies(RootPath, CaseName)
    FileCount = {"redundant": 30, "count": 41, "policy": 1}.get(CaseName, 3)
    FileNames = WriteSources(RootPath, FileCount, "A", CaseName)
    BeforeSha = CommitSources(RootPath)
    ChangedNames = WriteSources(RootPath, FileCount, "B", CaseName)
    assert ChangedNames == FileNames
    HeadValue = CommitSources(RootPath)
    BranchData = GitCommand(RootPath, "checkout", "-b", "target", BeforeSha)
    assert not BranchData
    TargetNames = WriteSources(RootPath, FileCount, "C", CaseName)
    assert TargetNames == FileNames
    TargetSha = CommitSources(RootPath)
    assert GitCommand(RootPath, "merge-base", HeadValue, TargetSha).strip() == BeforeSha
    return BeforeSha, HeadValue, TargetSha, FileNames


# fixture commits use only their private repository and never publish or execute a hook
def CommitSources(RootPath: Path) -> str:
    StagedData = GitCommand(RootPath, "add", "--all")
    assert not StagedData
    CommitData = GitCommand(
        RootPath,
        "-c",
        "commit.gpgsign=false",
        "commit",
        "--allow-empty",
        "-m",
        "context fixture",
    )
    assert "context fixture" in CommitData
    return GitCommand(RootPath, "rev-parse", "HEAD").strip()
