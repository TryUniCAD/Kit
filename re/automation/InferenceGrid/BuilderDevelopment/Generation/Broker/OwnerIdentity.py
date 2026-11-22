# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import kill
from sys import platform

from Processes import process_start


# uncertain process inspection never permits taking over a possibly live controller endpoint
def OwnerIdentity(Pid):
    if platform == "win32":
        from ApplicationWorkers.WindowsIdentity import process_start as WindowsIdentity

        return WindowsIdentity(Pid)
    Identity = process_start(Pid, live=True)
    if Identity is not None:
        return Identity
    try:
        kill(Pid, 0)
    except ProcessLookupError:
        return None
    except PermissionError as Error:
        raise OSError(
            "provider_unavailable: controller ownership inspection was denied"
        ) from Error
    raise OSError("provider_unavailable: controller ownership inspection is uncertain")
