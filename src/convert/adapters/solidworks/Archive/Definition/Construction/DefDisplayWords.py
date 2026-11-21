# signed display words represent the full authored pair of bit fields without narrowing it
def DefDisplayWords(BitsValue: tuple[int, ...]) -> tuple[int, int]:
    FlagMask = sum(1 << FlagBit for FlagBit in set(BitsValue))
    LowWord = FlagMask & 0xFFFFFFFF
    HighWord = FlagMask >> 32
    return (LowWord ^ 0x80000000) - 0x80000000, (HighWord ^ 0x80000000) - 0x80000000
