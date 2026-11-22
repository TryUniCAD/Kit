from pathlib import Path as FilePath
from shutil import which as FindProgram
from sys import platform as KPlatform


# native windows reporting must use git bash rather than the unrelated subsystem launcher on path
def FindTestShell() -> str:
    if KPlatform != "win32":
        return "bash"
    GitProgram = FindProgram("git")
    if GitProgram is None:
        raise FileNotFoundError("native Windows reporting requires Git for Windows")
    ShellPath = FilePath(GitProgram).resolve().parent.parent / "bin" / "bash.exe"
    if not ShellPath.is_file():
        raise FileNotFoundError(f"Git Bash was not found at {ShellPath}")
    return str(ShellPath)
