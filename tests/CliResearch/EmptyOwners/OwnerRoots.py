from collections.abc import Iterator
from contextlib import contextmanager as ContextManager
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from tests.CliResearch.OpenLegacy import OpenLegacy


# separate pinned repositories preserve both producer contracts without weakening their clean checkout guards
@ContextManager
def OwnerRoots(
    RootPath: FilePath, ParentPath: FilePath
) -> Iterator[tuple[FilePath, FilePath]]:
    ReaderPath = ParentPath / "Reader"
    PropertyPath = ParentPath / "Property"
    ReaderPath.mkdir()
    PropertyPath.mkdir()
    with (
        OpenLegacy(
            RootPath, ReaderPath, "c0a401a607759fb0c2589647c2a22af65ebb7ce1"
        ) as ReaderRoot,
        OpenLegacy(
            RootPath, PropertyPath, "5fb7e7737f0b9af52373da5e3f4556cd83ba8607"
        ) as PropertyRoot,
    ):
        for Arguments in (
            (
                "sparse-checkout",
                "add",
                "re/solidworks/PropertyBoundary",
                "re/solidworks/EncoderBoundary",
            ),
            ("read-tree", "-mu", "HEAD"),
        ):
            _ = RunProcess(
                ("git", "-C", str(PropertyRoot), *Arguments),
                capture_output=True,
                text=True,
                check=True,
                timeout=120,
            )
        yield ReaderRoot, PropertyRoot
