from convert.adapters.solidworks.Archive.Exchange.HashUnqliteKey import (
    HashUnqliteKey,
)
from convert.adapters.solidworks.Archive.Exchange.UnqliteLayout import (
    KUnqliteMap,
    KUnqlitePager,
    KUnqlitePageSize,
)


# fresh single-bucket files derive their engine declaration and page map from the implemented storage rules
def UnqliteHeaders(ClockValue: int) -> bytes:
    if type(ClockValue) is not int or not 0 <= ClockValue <= 0xFFFFFFFF:
        raise ValueError("invalid UnQLite clock word")
    Engine = b"hash"
    Pager = (
        KUnqlitePager.pack(
            b"unqlite", 0xDB7C2712, ClockValue, 512, KUnqlitePageSize, len(Engine)
        )
        + Engine
    )
    BucketMap = KUnqliteMap.pack(
        0xFA782DCB, HashUnqliteKey(b"chm@symisc"), 0, 0, 1, 0, 1, 0, 2
    )
    return Pager.ljust(KUnqlitePageSize, b"\0") + BucketMap.ljust(
        KUnqlitePageSize, b"\0"
    )
