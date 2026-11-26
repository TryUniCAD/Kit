# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from importlib import import_module as ImportModule
from typing import cast as CastValue


# dynamic research process identities remain observable without importing excluded implementation sources
def LiveStart(ProcessId: int) -> str | None:
    return CastValue(
        str | None, ImportModule("Processes").process_start(ProcessId, live=True)
    )
