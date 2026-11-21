# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from sys import argv as ArgValues, path as SearchPaths, stdin as InputStream

# the fixture must import the tested checkout without inheriting another research root
KRepoRoot = FilePath(__file__).resolve().parents[4]
SearchPaths.insert(0, str(KRepoRoot / "re/automation"))

from InferenceGrid.BuilderDevelopment.StageState import HoldBuilderRun


# a second operating system process must own the lock during competing resume
def HoldOwner() -> None:
    RunPath = FilePath(ArgValues[1])
    with HoldBuilderRun(RunPath):
        print("ready", flush=True)
        InputStream.readline()


if __name__ == "__main__":
    HoldOwner()
