# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import sys as System
from subprocess import Popen as StartProcess


# research children need independent process groups for targeted cancellation without interrupting the launcher
def StartResearch(
    Arguments: list[str], OwnWindows: bool = False
) -> StartProcess[bytes]:
    if System.platform == "win32":
        if OwnWindows:
            from subprocess import CREATE_NEW_PROCESS_GROUP as KNewProcessGroup

            return StartProcess(Arguments, creationflags=KNewProcessGroup)
    return StartProcess(Arguments, start_new_session=System.platform != "win32")
