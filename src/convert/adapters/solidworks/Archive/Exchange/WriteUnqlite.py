from collections.abc import Sequence

from convert.adapters.solidworks.Archive.Exchange.UnqliteHeaders import (
    UnqliteHeaders,
)
from convert.adapters.solidworks.Archive.Exchange.WriteDbBucket import (
    WriteDbBucket,
)


# callers synthesize all three pages from the chosen publication clock and ordered live entries
def WriteUnqlite(ClockValue: int, Records: Sequence[tuple[bytes, bytes]]) -> bytes:
    return UnqliteHeaders(ClockValue) + WriteDbBucket(Records)
