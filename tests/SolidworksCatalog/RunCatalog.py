# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonPath


# subprocess boundaries verify catalogue tools without importing research code into tests
def RunCatalog(ToolName: str, *Arguments: str) -> CompletedProcess[str]:
    RepoRoot = FilePath(__file__).resolve().parents[2]
    ToolPath = RepoRoot / "re" / "Solidworks" / "PlannerCatalog" / ToolName
    return RunProcess(
        [PythonPath, "-B", str(ToolPath), *Arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
