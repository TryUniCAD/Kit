# the default profile constructor samples filetime while other sheet features use owner constructor zeros
def MakeProfileTime(SecondsValue: int) -> dict[str, object]:
    TicksValue = (SecondsValue + 11644473600) * 10000000
    LowerValue = TicksValue & 4294967295
    UpperValue = TicksValue >> 32
    return {
        "f2a0": LowerValue - 4294967296 if LowerValue & 2147483648 else LowerValue,
        "f2a4": UpperValue - 4294967296 if UpperValue & 2147483648 else UpperValue,
    }
