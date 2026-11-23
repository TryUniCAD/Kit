# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from signal import SIGINT, SIGTERM
from sys import platform as KPlatform


# platform signal ownership must preserve ordinary windows readers while enabling supervised cancellation
def SelectSignals(OwnWindows: bool) -> list[int]:
    if KPlatform == "win32":
        if not OwnWindows:
            return []
        from signal import SIGBREAK

        return [SIGINT, SIGTERM, SIGBREAK]
    from signal import SIGCONT, SIGHUP, SIGQUIT, SIGTSTP, SIGUSR1, SIGUSR2

    return [SIGINT, SIGTERM, SIGHUP, SIGQUIT, SIGUSR1, SIGUSR2, SIGTSTP, SIGCONT]
