from convert.adapters.solidworks.Archive.Exchange.ReadUnqliteCell import (
    ReadUnqliteCell,
)
from convert.adapters.solidworks.Archive.Exchange.ReadUnqliteFree import (
    ReadUnqliteFree,
)
from convert.adapters.solidworks.Archive.Exchange.UnqliteLayout import (
    KUnqliteBucket,
    KUnqlitePageSize,
)


# the live chain retains logical insertion order even when updates move records into earlier holes
def ReadDbBucket(Bucket: bytes) -> tuple[tuple[bytes, bytes], ...]:
    if len(Bucket) != KUnqlitePageSize:
        raise ValueError("UnQLite bucket must occupy one complete page")
    Offset, FreeOffset, Slave = KUnqliteBucket.unpack_from(Bucket)
    if not Offset or Slave:
        raise ValueError("UnQLite bucket requires local populated records")
    Ranges = ReadUnqliteFree(Bucket, FreeOffset)
    Records: list[tuple[bytes, bytes]] = []
    Visited: set[int] = set()
    LiveKeys: set[bytes] = set()
    while Offset:
        if Offset in Visited:
            raise ValueError("UnQLite active cell list contains a cycle")
        Following, CellEnd, KeyValue, DataValue = ReadUnqliteCell(Bucket, Offset)
        if KeyValue in LiveKeys:
            raise ValueError("UnQLite active cells repeat a key")
        Ranges.append((Offset, CellEnd))
        Records.append((KeyValue, DataValue))
        Visited.add(Offset)
        LiveKeys.add(KeyValue)
        Offset = Following
    RequiredStart = KUnqliteBucket.size
    for RegionStart, RegionEnd in sorted(Ranges):
        if RegionStart != RequiredStart:
            raise ValueError(
                "UnQLite bucket regions overlap or leave unallocated space"
            )
        RequiredStart = RegionEnd
    if RequiredStart != len(Bucket):
        raise ValueError("UnQLite bucket has unallocated trailing space")
    return tuple(reversed(Records))
