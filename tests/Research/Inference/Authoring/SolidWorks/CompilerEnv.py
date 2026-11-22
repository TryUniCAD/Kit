# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ
from pathlib import Path


# fixed powershell expressions pass native path values without interpreting them as command text
def CompilerEnv(
    ScriptPath: Path,
    CasePath: Path,
    OutputPath: Path,
    ExePath: Path,
    Interop: Path,
    ShellPath: Path,
) -> dict[str, str]:
    Environment = dict(environ)
    Environment.update(
        {
            "SystemRoot": str(ShellPath.parents[3]),
            "WINDIR": str(ShellPath.parents[3]),
            "KIT_COMPILE_SCRIPT": str(ScriptPath),
            "KIT_COMPILE_CASE": str(CasePath),
            "KIT_COMPILE_OUTPUT": str(OutputPath),
            "KIT_COMPILE_EXECUTABLE": str(ExePath),
            "KIT_COMPILE_INTEROP": str(Interop),
        }
    )
    return Environment
