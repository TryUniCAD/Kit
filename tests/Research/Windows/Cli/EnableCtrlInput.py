# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import sys
from collections.abc import Callable
from typing import cast as CastValue

if sys.platform == "win32":
    from win32api import SetConsoleCtrlHandler


# the private console must enable inheritable control delivery before starting its installed launcher
def EnableCtrlInput() -> None:
    if sys.platform == "win32":
        CastValue(Callable[[None, bool], None], SetConsoleCtrlHandler)(None, False)
    else:
        raise OSError("Native console control requires Windows")
