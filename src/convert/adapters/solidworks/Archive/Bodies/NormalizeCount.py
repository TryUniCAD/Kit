from convert.adapters.solidworks.Archive.Bodies.ApplyCountMode import ApplyCountMode


# native count interpretations must retain signed wire words while bounding actual repetition
def NormalizeCount(CountValue: int, ModeValue: str) -> int:
    CountValue = ApplyCountMode(CountValue, ModeValue)
    if not 0 <= CountValue <= 10_000_000:
        raise ValueError(f"implausible SOLIDWORKS body repeat {CountValue}")
    return CountValue
