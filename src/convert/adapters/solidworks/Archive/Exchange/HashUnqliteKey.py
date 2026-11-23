# the shared hash must agree for both the engine probe word and each active key
def HashUnqliteKey(KeyValue: bytes) -> int:
    HashValue = 5381
    for ByteValue in KeyValue[:2048]:
        HashValue = (HashValue * 33 + ByteValue) & 0xFFFFFFFF
    return HashValue
