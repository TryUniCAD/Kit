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
    GitPath = FilePath(GitProgram).resolve()
    for RootPath in (GitPath.parent.parent, GitPath.parent.parent.parent):
        ShellPath = RootPath / "bin" / "bash.exe"
        if ShellPath.is_file():
            return str(ShellPath)
    raise FileNotFoundError("Git for Windows has no native Bash executable")
