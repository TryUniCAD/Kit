from struct import pack as PackValues

# the 255th unit activates the archive string length word
KChildLabel = "c" * 255


# expected bytes are specified independently of the field and map codecs
def MakeValueWire(LabelFrame: bytes) -> bytes:
    return (
        PackValues("<HHH", 0xFFFF, 1, 9)
        + b"ValueRoot"
        + PackValues("<i", -29)
        + LabelFrame
        + PackValues("<HHHH", 3, 0xFFFF, 1, 10)
        + b"ValueChild"
        + b"\xff\xfe\xff\xff\xff\x00"
        + KChildLabel.encode("utf-16-le")
        + PackValues("<HHH", 2, 4, 0)
    )
