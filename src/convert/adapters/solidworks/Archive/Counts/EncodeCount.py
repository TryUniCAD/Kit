from struct import pack as PackValue


# native count widths must follow model cardinality without saved payloads
def EncodeCount(CountValue: int, *, IsFramework: bool = False) -> bytes:
    if type(CountValue) is not int or type(IsFramework) is not bool:
        raise TypeError(
            "archive counts require an integer and an explicit boolean domain"
        )
    UpperLimit = (1 << 64) - 1 if IsFramework else (1 << 32) - 1
    if not 0 <= CountValue <= UpperLimit:
        raise ValueError("archive count exceeds its unsigned domain")
    if CountValue < 0xFFFF:
        return PackValue("<H", CountValue)
    if not IsFramework or CountValue < 0xFFFFFFFF:
        return PackValue("<HI", 0xFFFF, CountValue)
    return PackValue("<HIQ", 0xFFFF, 0xFFFFFFFF, CountValue)
