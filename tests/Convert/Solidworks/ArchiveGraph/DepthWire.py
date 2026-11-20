from struct import pack as PackValues


# independent wire records anchor the open body limit and terminal references
def DepthWire(BodyCount: int) -> tuple[bytes, bytes]:
    RootValue = b"\xff\xff\x01\x00\x04\x00Root" + PackValues("<iH", 11, 1)
    LeafValue = b"\xff\xff\x02\x00\x04\x00Leaf" + PackValues("<iH", 29, 1)
    NestedValue = b"\x03\x80" + PackValues("<iH", 29, 1)
    TerminalValue = b"\x03\x80" + PackValues("<iHHH", 29, 2, 2, 0)
    PrimaryValue = RootValue + LeafValue + NestedValue * (BodyCount - 3) + TerminalValue
    NextValue = BodyCount + 3
    LinkedValue = (
        PackValues("<I", NextValue)
        + b"\x03\x80"
        + PackValues("<iHHH", 41, 2, NextValue - 1, 2)
    )
    return PrimaryValue, LinkedValue
