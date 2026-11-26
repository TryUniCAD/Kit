# native count interpretation must also be available for comparing stale source words
def ApplyCountMode(CountValue: int, ModeValue: str) -> int:
    if ModeValue == "Positive":
        return max(CountValue, 0)
    if ModeValue == "Unsigned":
        return CountValue & 0xFFFFFFFF
    if ModeValue == "SignedPositive":
        CountValue &= 0xFFFFFFFF
        return CountValue if CountValue < 0x80000000 else 0
    if ModeValue != "":
        raise ValueError(f"unsupported native array count mode {ModeValue}")
    return CountValue
