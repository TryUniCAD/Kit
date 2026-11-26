from struct import pack as PackValues

# independent header bytes place the revision at absolute position four
KWireHeader = b"\x04\x00\x00\x00\x01\x00\x00\x00"


# an independent wire expectation catches matching mistakes in both processes
def CanonicalWire() -> bytes:
    return b"".join(
        (
            KWireHeader,
            b"\x02\x00\xff\xff",
            b"\xff\xfe\xff\x03a\x00\x3d\xd8\x08\xdc",
            b"\xff" * 6,
            b"\xff" * 10 + b"\x00" * 4,
            b"\x02\x00",
            b"\xfe\xff\xff\xfe\xff\x00",
            PackValues("<ifd", -7, 1.5, 2.25),
            b"\xff\x7f\xff\x7f\x00\x00",
            b"\xff\xfe\xff\x03R\x00o\x00w\x00",
            PackValues("<ifd", 18, -2.5, 0.125),
            b"\xff\x7f\xff\x7f\x00\x80",
            b"\xff\xfe\xff\xff\xff\x00" + b"z\x00" * 255,
            b"\xfe\xff\xff\xff\xfe\xff\xff\xff\x02\x00",
            b"\x02\x00\xff\xfe\xff\xff\xff\xff\xfe\xff\x00\x00",
            b"z\x00" * 65532,
            b"\x3d\xd8\x08\xdc",
            PackValues("<ifd", 120, 0.25, 0.5),
            b"\x00\x00\xff\xfe\xff\x01x\x00",
            PackValues("<ifd", -2147483648, 0.5, -1.0),
        )
    )
