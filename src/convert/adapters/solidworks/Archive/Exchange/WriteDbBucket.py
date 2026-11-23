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
def WriteDbBucket(Records: Sequence[tuple[object, object]]) -> bytes:
    OutputPage = bytearray(KUnqlitePageSize)
    Offset = KUnqliteBucket.size
    Previous = 0
    LiveKeys: set[bytes] = set()
    for KeyValue, DataValue in Records:
        if (
            not isinstance(KeyValue, bytes)
            or not isinstance(DataValue, bytes)
            or not KeyValue
            or KeyValue in LiveKeys
        ):
            raise ValueError("UnQLite bucket needs distinct nonempty byte keys")
        CellSize = KUnqliteCell.size + len(KeyValue) + len(DataValue)
        CellEnd = Offset + CellSize
        if (
            CellSize >= KUnqlitePageSize // 2
            or CellEnd + KUnqliteFree.size > KUnqlitePageSize
        ):
            raise ValueError("record needs a larger or overflow UnQLite bucket")
        KUnqliteCell.pack_into(
            OutputPage,
            Offset,
            HashUnqliteKey(KeyValue),
            len(KeyValue),
            len(DataValue),
            Previous,
            0,
        )
        OutputPage[Offset + KUnqliteCell.size : CellEnd] = KeyValue + DataValue
        LiveKeys.add(KeyValue)
        Previous, Offset = Offset, CellEnd
    if not LiveKeys:
        raise ValueError("a fresh populated UnQLite bucket needs at least one record")
    KUnqliteBucket.pack_into(OutputPage, 0, Previous, Offset, 0)
    KUnqliteFree.pack_into(OutputPage, Offset, 0, KUnqlitePageSize - Offset)
    return bytes(OutputPage)
