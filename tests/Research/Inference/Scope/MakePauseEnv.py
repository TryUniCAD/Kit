# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ as Environment, pathsep as PathSeparator
from pathlib import Path as FilePath
from shutil import copyfile as CopyFile

from tests.Research.SupervisorClient import KRepoRoot


# private startup configuration isolates the first catalogue supervisor from other runs
def MakePauseEnv(ReadyPath: FilePath, PausePath: FilePath) -> dict[str, str]:
    Startup = ReadyPath.parent / "PauseStartup"
    Startup.mkdir()
    SitePath = CopyFile(
        FilePath(__file__).with_name("PauseOnSettlement.py"),
        Startup / "sitecustomize.py",
    )
    PythonPaths = [str(SitePath.parent), str(KRepoRoot)]
    if Existing := Environment.get("PYTHONPATH"):
        PythonPaths.append(Existing)
    return {
        **Environment,
        "PYTHONPATH": PathSeparator.join(PythonPaths),
        "KIT_TEST_PAUSE_OWNER": str(KRepoRoot / "re/automation/Supervisor.py"),
        "KIT_TEST_PAUSE_READY": str(ReadyPath),
        "KIT_TEST_PAUSE_MARKER": str(PausePath),
    }
