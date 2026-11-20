from struct import pack as PackValues


# independent slot and tag bytes expose mistakes shared by the reader and writer
def ExpectedWire() -> tuple[bytes, bytes]:
    PrimaryValue = b"".join(
        (
            b"\xff\xff\x01\x00\x04\x00Root",
            PackValues("<iH", 11, 4),
            b"\xff\xff\x02\x00\x04\x00Leaf",
            PackValues("<iH", 29, 2),
            b"\x02\x00\x00\x00",
            b"\x04\x00\x03\x80",
            PackValues("<iH", 29, 2),
            b"\x02\x00\x00\x00\x02\x00",
        )
    )
    LinkedValue = b"".join(
        (
            PackValues("<I", 6),
            b"\x03\x80",
            PackValues("<iH", 41, 3),
            b"\x04\x00\x02\x00\x06\x00",
        )
    )
    return PrimaryValue, LinkedValue
