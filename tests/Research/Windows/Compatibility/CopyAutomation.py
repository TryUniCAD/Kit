from pathlib import Path as FilePath
from shutil import copyfile as CopyFile
from subprocess import run as RunProcess


# compatibility fixtures need tracked runtime source without captures caches or unrelated research output
def CopyAutomation(RepoRoot: FilePath, RootPath: FilePath) -> None:
    SourceRoot = RepoRoot.resolve()
    TargetRoot = RootPath.resolve()
    SourceList = RunProcess(
        ["git", "-C", str(SourceRoot), "ls-files", "-z", "--", "re/automation"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    for RepoName in SourceList.stdout.split("\0"):
        if not RepoName or FilePath(RepoName).suffix != ".py":
            continue
        SourcePath = (SourceRoot / RepoName).resolve()
        TargetPath = (TargetRoot / RepoName).resolve()
        if not SourcePath.is_relative_to(SourceRoot):
            raise ValueError("Automation source escapes the selected repository")
        if not TargetPath.is_relative_to(TargetRoot):
            raise ValueError("Automation destination escapes the private fixture")
        TargetPath.parent.mkdir(parents=True, exist_ok=True)
        _ = CopyFile(SourcePath, TargetPath)
