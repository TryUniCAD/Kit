from collections.abc import Sequence

from convert.adapters.solidworks.Archive.Exchange.HashUnqliteKey import (
    HashUnqliteKey,
)
from convert.adapters.solidworks.Archive.Exchange.UnqliteLayout import (
    KUnqliteBucket,
    KUnqliteCell,
    KUnqliteFree,
    KUnqlitePageSize,
)


# a new local bucket allocates only live records and leaves one initialized free region
def WriteUnqliteBucket(Records: Sequence[tuple[bytes, bytes]]) -> bytes:
    Page = bytearray(KUnqlitePageSize)
    Offset = KUnqliteBucket.size
    Previous = 0
    Keys: set[bytes] = set()
    for KeyValue, DataValue in Records:
        if (
            not isinstance(KeyValue, bytes)
            or not isinstance(DataValue, bytes)
            or not KeyValue
            or KeyValue in Keys
        ):
            raise ValueError("UnQLite bucket needs distinct nonempty byte keys")
        CellSize = KUnqliteCell.size + len(KeyValue) + len(DataValue)
        End = Offset + CellSize
        if (
            CellSize >= KUnqlitePageSize // 2
            or End + KUnqliteFree.size > KUnqlitePageSize
        ):
            raise ValueError("record needs a larger or overflow UnQLite bucket")
        KUnqliteCell.pack_into(
            Page,
            Offset,
            HashUnqliteKey(KeyValue),
            len(KeyValue),
            len(DataValue),
            Previous,
            0,
        )
        Page[Offset + KUnqliteCell.size : End] = KeyValue + DataValue
        Keys.add(KeyValue)
        Previous, Offset = Offset, End
    if not Keys:
        raise ValueError("a fresh populated UnQLite bucket needs at least one record")
    KUnqliteBucket.pack_into(Page, 0, Previous, Offset, 0)
    KUnqliteFree.pack_into(Page, Offset, 0, KUnqlitePageSize - Offset)
    return bytes(Page)
