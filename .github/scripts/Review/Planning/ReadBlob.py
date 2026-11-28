import subprocess as ProcessTools
from pathlib import PurePosixPath


# reconstruction must consume bounded immutable objects without interpreting proposed paths as commands
def ReadBlob(Revision: str, FileName: str) -> bytes:
    if (
        len(Revision) != 40
        or any(Letter not in "0123456789abcdef" for Letter in Revision)
        or not FileName
        or ":" in FileName
        or "\\" in FileName
        or PurePosixPath(FileName).is_absolute()
        or any(PartName in ("", ".", "..") for PartName in FileName.split("/"))
    ):
        raise ValueError("Invalid planning object identity")
    ObjectName = f"{Revision}:{FileName}"
    ModeInfo = ProcessTools.run(
        ["git", "--literal-pathspecs", "ls-tree", Revision, "--", FileName],
        capture_output=True,
        check=True,
        timeout=30,
    )
    if len(ModeInfo.stdout.splitlines()) != 1 or not ModeInfo.stdout.startswith(
        (b"100644 blob ", b"100755 blob ")
    ):
        raise ValueError("Planning reconstruction requires regular Git files")
    ObjectSize = ProcessTools.run(
        ["git", "cat-file", "-s", ObjectName],
        capture_output=True,
        check=True,
        timeout=30,
    )
    if not 0 <= int(ObjectSize.stdout) <= 32_000_000:
        raise ValueError("Planning object exceeds verification limit")
    return ProcessTools.run(
        ["git", "show", ObjectName],
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout
