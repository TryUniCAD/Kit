# modeled registration epochs must supply the native filetime words without reading a saved feature or clock
def FeatureTime(CreatedValue: int) -> dict[str, int]:
    if type(CreatedValue) is not int or not 0 <= CreatedValue <= 0xFFFFFFFF:
        raise ValueError("feature creation time must fit unsigned unix seconds")
    TickValue = (CreatedValue + 11644473600) * 10_000_000
    LowValue, HighValue = TickValue & 0xFFFFFFFF, TickValue >> 32
    return {
        "f2a0": LowValue - (1 << 32) if LowValue & (1 << 31) else LowValue,
        "f2a4": HighValue - (1 << 32) if HighValue & (1 << 31) else HighValue,
    }
