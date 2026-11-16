from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager as ContextManager
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory as TempDirectory

from tests.Convert.Solidworks.Research.Frozen.MakeFrozen import MakeFrozen


# isolated temporary sources preserve old measurements while the shared model continues to change
@ContextManager
def FrozenRoot() -> Iterator[FilePath]:
    with TempDirectory(prefix="sw-frozen-") as FolderName:
        SourceRoot = FilePath(FolderName)
        MakeFrozen(SourceRoot)
        yield SourceRoot
