from convert.adapters.solidworks.Archive.Exchange.UnqliteLayout import (
    KUnqliteBucket,
    KUnqliteFree,
)


# the free list contributes only checked extents so inactive disk residues never become records
def ReadUnqliteFree(Bucket: bytes, StartOffset: int) -> list[tuple[int, int]]:
    Ranges: list[tuple[int, int]] = []
    Visited: set[int] = set()
    Current = StartOffset
    while Current:
        if (
            Current in Visited
            or Current < KUnqliteBucket.size
            or Current + KUnqliteFree.size > len(Bucket)
        ):
            raise ValueError("UnQLite bucket has an invalid free-list link")
        Following, BlockLength = KUnqliteFree.unpack_from(Bucket, Current)
        BlockEnd = Current + BlockLength
        if BlockLength < KUnqliteFree.size or BlockEnd > len(Bucket):
            raise ValueError("UnQLite free block is outside its bucket")
        Ranges.append((Current, BlockEnd))
        Visited.add(Current)
        Current = Following
    return Ranges
