# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from contextlib import AbstractContextManager
from importlib import import_module as ImportModule
from typing import Callable, cast as CastValue
from pathlib import Path as FilePath
from sys import argv as ArgValues, path as SearchPaths, stdin as InputStream

# the fixture must import the tested checkout without inheriting another research root
KRepoRoot = FilePath(__file__).resolve().parents[4]

SearchPaths.insert(0, str(KRepoRoot))
SearchPaths.insert(0, str(KRepoRoot / "re/automation"))


# a second operating system process must own the lock during competing resume
def HoldOwner() -> None:
    HoldRun = CastValue(
        Callable[[FilePath], AbstractContextManager[None]],
        ImportModule("InferenceGrid.BuilderDevelopment.StageState").HoldBuilderRun,
    )
    RunPath = FilePath(ArgValues[1])
    with HoldRun(RunPath):
        print("ready", flush=True)
        _ = InputStream.readline()


if __name__ == "__main__":
    HoldOwner()
