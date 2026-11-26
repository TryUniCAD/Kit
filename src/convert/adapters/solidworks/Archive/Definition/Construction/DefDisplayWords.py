# signed display words represent the full authored pair of bit fields without narrowing it
def DefDisplayWords(BitsValue: tuple[int, ...]) -> tuple[int, int]:
    BitMask = sum(1 << Index for Index in set(BitsValue))
    LowValue = BitMask & 0xFFFFFFFF
    HighValue = BitMask >> 32
    return (LowValue ^ 0x80000000) - 0x80000000, (HighValue ^ 0x80000000) - 0x80000000
