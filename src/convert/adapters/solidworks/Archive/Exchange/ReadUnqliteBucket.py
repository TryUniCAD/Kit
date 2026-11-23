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
def ReadUnqliteBucket(Bucket: bytes) -> tuple[tuple[bytes, bytes], ...]:
    if len(Bucket) != KUnqlitePageSize:
        raise ValueError("UnQLite bucket must occupy one complete page")
    Offset, Free, Slave = KUnqliteBucket.unpack_from(Bucket)
    if not Offset or Slave:
        raise ValueError("UnQLite bucket requires local populated records")
    Ranges = ReadUnqliteFree(Bucket, Free)
    Records: list[tuple[bytes, bytes]] = []
    Visited: set[int] = set()
    Keys: set[bytes] = set()
    while Offset:
        if Offset in Visited:
            raise ValueError("UnQLite active cell list contains a cycle")
        Following, End, KeyValue, DataValue = ReadUnqliteCell(Bucket, Offset)
        if KeyValue in Keys:
            raise ValueError("UnQLite active cells repeat a key")
        Ranges.append((Offset, End))
        Records.append((KeyValue, DataValue))
        Visited.add(Offset)
        Keys.add(KeyValue)
        Offset = Following
    End = KUnqliteBucket.size
    for Start, Stop in sorted(Ranges):
        if Start != End:
            raise ValueError(
                "UnQLite bucket regions overlap or leave unallocated space"
            )
        End = Stop
    if End != len(Bucket):
        raise ValueError("UnQLite bucket has unallocated trailing space")
    return tuple(reversed(Records))
