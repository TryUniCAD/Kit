# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ as ProcessEnv
from pathlib import Path as FilePath
from tempfile import gettempdir as TempRoot

from convert.Security.PathBoundary import ResolveWithin, UnsafePath


# supervised fixtures may access their exact session while temporary writes remain scoped to its work directory
def ResolveSession(PathValue: str) -> FilePath:
    ScratchPath = FilePath(TempRoot()).resolve(strict=True)
    SessionPath = ResolveWithin(PathValue, ScratchPath.parent)
    if (
        ScratchPath.name != "work"
        or SessionPath != ScratchPath.parent
        or ProcessEnv.get("KIT_SESSION") != str(SessionPath)
    ):
        raise UnsafePath("path escapes trusted root for fixture session")
    return SessionPath
