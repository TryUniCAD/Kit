# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Write a fresh one-bucket UnQLite database from bounded key and value records."""

from collections.abc import Sequence
from datetime import datetime

from convert.adapters.solidworks.Archive.Exchange.WriteUnqlite import (
    WriteUnqlite,
)


# the original research inputs keep their established packed month convention
def DosClock(Created: datetime) -> int:
    if Created.tzinfo is not None or not 1980 <= Created.year <= 2107:
        raise ValueError("UnQLite creation clock must be a DOS-range local wall time")
    return (
        (Created.year - 1980) << 25
        | Created.month << 21
        | Created.day << 16
        | Created.hour << 11
        | Created.minute << 5
        | Created.second // 2
    )


# the standalone research callers use the shared physical store writer
def WriteSingleBucket(
    Created: datetime, Records: Sequence[tuple[bytes, bytes]]
) -> bytes:
    return WriteUnqlite(DosClock(Created), Records)
