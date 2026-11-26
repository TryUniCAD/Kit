from convert.adapters.solidworks.Archive.Bodies.ApplyCountMode import ApplyCountMode


# stale wire words must not prevent writing a valid modeled repetition
def SelectCountWord(WireValue: object, ItemCount: int, ModeValue: str) -> int:
    Candidate = WireValue if type(WireValue) is int else ItemCount
    if ApplyCountMode(Candidate, ModeValue) == ItemCount:
        return Candidate
    return ItemCount
