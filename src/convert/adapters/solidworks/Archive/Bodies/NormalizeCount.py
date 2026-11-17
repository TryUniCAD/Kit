# native count interpretations must retain signed wire words while bounding actual repetition
def NormalizeCount(CountValue: int, ModeValue: str) -> int:
    if ModeValue == "Positive":
        CountValue = max(CountValue, 0)
    elif ModeValue == "Unsigned":
        CountValue &= 0xFFFFFFFF
    elif ModeValue != "":
        raise ValueError(f"unsupported native array count mode {ModeValue}")
    if not 0 <= CountValue <= 10_000_000:
        raise ValueError(f"implausible SOLIDWORKS body repeat {CountValue}")
    return CountValue
