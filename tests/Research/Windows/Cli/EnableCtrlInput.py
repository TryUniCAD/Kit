# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable
from sys import platform as KPlatform
from typing import cast as CastValue

if KPlatform == "win32":
    from win32api import SetConsoleCtrlHandler


# the private console must enable inheritable control delivery before starting its installed launcher
def EnableCtrlInput() -> None:
    if KPlatform == "win32":
        CastValue(Callable[[None, bool], None], SetConsoleCtrlHandler)(None, False)
    else:
        raise OSError("Native console control requires Windows")
