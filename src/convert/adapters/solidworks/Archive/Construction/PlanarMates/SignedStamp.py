# reference wrapper access epochs preserve native unsigned bits in their signed archive word
def SignedStamp(Value: int) -> int:
    if type(Value) is not int or not 0 <= Value <= 0xFFFFFFFF:
        raise ValueError("wrapper access stamp must fit native unsigned word")
    return Value if Value < 0x80000000 else Value - 0x100000000
