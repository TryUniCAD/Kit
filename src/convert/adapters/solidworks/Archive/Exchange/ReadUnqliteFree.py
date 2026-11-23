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
        Following, Size = KUnqliteFree.unpack_from(Bucket, Current)
        End = Current + Size
        if Size < KUnqliteFree.size or End > len(Bucket):
            raise ValueError("UnQLite free block is outside its bucket")
        Ranges.append((Current, End))
        Visited.add(Current)
        Current = Following
    return Ranges
