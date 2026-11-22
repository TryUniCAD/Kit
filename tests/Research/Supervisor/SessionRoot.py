# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ as Environment
from pathlib import Path as FilePath
from tempfile import gettempdir as GetTempDir


# the supervisor binds its private work directory and session argument independently at launch
def SessionRoot(SessionArg: str) -> FilePath:
    WorkPath = FilePath(GetTempDir()).resolve(strict=True)
    if WorkPath.name != "work" or any(
        FilePath(Value) != WorkPath.parent
        for Value in (SessionArg, Environment["KIT_SESSION"])
    ):
        raise ValueError("worker session differs from its private work directory")
    return WorkPath.parent
