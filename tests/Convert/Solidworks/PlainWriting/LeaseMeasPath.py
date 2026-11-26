from collections.abc import Iterator
from contextlib import contextmanager as ManagedScope
from os import name as OsName
from pathlib import Path as FilePath


# windows byte parity requires the exact native locator under an exclusively owned directory
@ManagedScope
def LeaseMeasPath(Folder: FilePath, NameValue: str) -> Iterator[FilePath]:
    if OsName != "nt":
        yield Folder / NameValue
        return
    NativeFolder = FilePath(r"C:\KitSdkCandidates")
    Target = NativeFolder / NameValue
    NativeFolder.mkdir()
    try:
        yield Target
    finally:
        Target.unlink(missing_ok=True)
        NativeFolder.rmdir()
