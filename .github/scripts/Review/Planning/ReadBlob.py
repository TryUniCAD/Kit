import subprocess as ProcessTools
from pathlib import PurePosixPath


# reconstruction must consume bounded immutable objects without interpreting proposed paths as commands
def ReadBlob(Revision: str, FileName: str) -> bytes:
    if (
        len(Revision) != 40
        or any(Letter not in "0123456789abcdef" for Letter in Revision)
        or not FileName
        or PurePosixPath(FileName).is_absolute()
        or any(PartName in ("", ".", "..") for PartName in FileName.split("/"))
    ):
        raise ValueError("Invalid planning object identity")
    ObjectName = f"{Revision}:{FileName}"
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
