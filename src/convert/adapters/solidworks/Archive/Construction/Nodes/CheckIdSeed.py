# allocator state must stay inside the signed native identity domain before reservations affect allocation
def CheckIdSeed(NextValue: int, Reserved: tuple[int, ...]) -> None:
    if type(NextValue) is not int or not 0 <= NextValue < 0x7FFFFFFF:
        raise ValueError("next persistent id must be a nonnegative signed integer")
    if type(Reserved) is not tuple or any(
        type(Value) is not int or not 0 <= Value < 0x7FFFFFFF for Value in Reserved
    ):
        raise ValueError("reserved persistent ids must be nonnegative signed integers")
