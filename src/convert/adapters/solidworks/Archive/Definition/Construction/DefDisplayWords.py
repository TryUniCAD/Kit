# signed display words represent the full authored pair of bit fields without narrowing it
def DefDisplayWords(BitsValue: tuple[int, ...]) -> tuple[int, int]:
    Mask = sum(1 << Bit for Bit in set(BitsValue))
    Low = Mask & 0xFFFFFFFF
    High = Mask >> 32
    return (Low ^ 0x80000000) - 0x80000000, (High ^ 0x80000000) - 0x80000000
