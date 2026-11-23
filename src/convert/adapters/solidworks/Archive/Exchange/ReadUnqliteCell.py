from convert.adapters.solidworks.Archive.Exchange.HashUnqliteKey import (
    HashUnqliteKey,
)
from convert.adapters.solidworks.Archive.Exchange.UnqliteLayout import (
    KUnqliteBucket,
    KUnqliteCell,
)


# local cell bounds and hash must be validated before a data payload can enter the model
def ReadUnqliteCell(Bucket: bytes, Offset: int) -> tuple[int, int, bytes, bytes]:
    KeyStart = Offset + KUnqliteCell.size
    if Offset < KUnqliteBucket.size or KeyStart > len(Bucket):
        raise ValueError("UnQLite active cell header is outside its bucket")
    HashValue, KeySize, DataSize, NextOffset, Overflow = KUnqliteCell.unpack_from(
        Bucket, Offset
    )
    DataStart = KeyStart + KeySize
    End = DataStart + DataSize
    if not KeySize or Overflow or End > len(Bucket):
        raise ValueError("UnQLite cell requires a complete local payload")
    KeyValue = Bucket[KeyStart:DataStart]
    if HashUnqliteKey(KeyValue) != HashValue:
        raise ValueError("UnQLite cell key hash differs")
    return NextOffset, End, KeyValue, Bucket[DataStart:End]
