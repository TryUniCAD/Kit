from convert.adapters.solidworks.Archive.Exchange.ReadUnqliteBucket import (
    ReadUnqliteBucket,
)
from convert.adapters.solidworks.Archive.Exchange.UnqliteHeaders import (
    UnqliteHeaders,
)
from convert.adapters.solidworks.Archive.Exchange.UnqliteLayout import (
    KUnqlitePager,
    KUnqlitePageSize,
)
from convert.adapters.solidworks.Archive.Exchange.UnqliteStore import UnqliteStore


# the ordinary exchange store is accepted only with its complete physical pager and unsplit map
def ReadUnqliteStore(Payload: bytes) -> UnqliteStore:
    if len(Payload) != 3 * KUnqlitePageSize:
        raise ValueError("UnQLite exchange store requires exactly three pages")
    _, _, ClockValue, _, _, _ = KUnqlitePager.unpack_from(Payload)
    BucketOffset = 2 * KUnqlitePageSize
    if Payload[:BucketOffset] != UnqliteHeaders(ClockValue):
        raise ValueError("UnQLite exchange store pager or bucket map differs")
    return UnqliteStore(ClockValue, ReadUnqliteBucket(Payload[BucketOffset:]))
