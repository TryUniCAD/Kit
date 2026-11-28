import subprocess as ProcessTools

from Input.ReadSource import ReadSource


# current target content exposes conflicting edits without treating unrelated target changes as proposed source
def ReadTarget(Revision: str, FileName: str) -> str | None:
    Result = ProcessTools.run(
        ["git", "cat-file", "-e", f"{Revision}:{FileName}"],
        capture_output=True,
        check=False,
        timeout=30,
    )
    if Result.returncode:
        return None
    return ReadSource(Revision, FileName)
