import os as OsTools
import subprocess as ProcessTools
from pathlib import Path
from tests.Policy.GeneratedCoverage.CopyPlan import CopyPlan


# real project inputs and isolated git objects exercise reconstruction without changing checkout state or publishing refs
def CreatePlan(TempPath: Path, CaseName: str) -> tuple[str, str, dict[str, str]]:
    RootPath = Path(__file__).resolve().parents[3]
    Revision = ProcessTools.run(
        ["git", "rev-parse", "HEAD"],
        cwd=RootPath,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    GitDir = ProcessTools.run(
        ["git", "rev-parse", "--absolute-git-dir"],
        cwd=RootPath,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    EnvState = {
        "PATH": OsTools.environ.get("PATH", OsTools.defpath),
        "GIT_DIR": GitDir,
        "GIT_WORK_TREE": str(TempPath),
        "GIT_INDEX_FILE": str(TempPath / "Index"),
        "GIT_AUTHOR_NAME": "Coverage process",
        "GIT_AUTHOR_EMAIL": "coverage@example.invalid",
        "GIT_COMMITTER_NAME": "Coverage process",
        "GIT_COMMITTER_EMAIL": "coverage@example.invalid",
    }
    ProcessTools.run(
        ["git", "read-tree", Revision], cwd=TempPath, env=EnvState, check=True
    )
    FileNames = CopyPlan(RootPath, TempPath, CaseName, EnvState)
    ProcessTools.run(
        ["git", "add", "--", *FileNames], cwd=TempPath, env=EnvState, check=True
    )
    TreeName = ProcessTools.run(
        ["git", "write-tree"],
        cwd=TempPath,
        env=EnvState,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    HeadSha = ProcessTools.run(
        ["git", "commit-tree", TreeName, "-p", Revision],
        input="coverage process\n",
        cwd=TempPath,
        env=EnvState,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return Revision, HeadSha, EnvState
