from struct import pack as PackValues

from tests.Convert.Solidworks.Archive.CanonicalWire import KWireHeader


# hand authored byte frames can detect changes in the source encoding flag
def AnsiWire() -> bytes:
    return b"".join(
        (
            KWireHeader,
            b"\x01\x00\x01\x00\x02\xe9\xff",
            b"\x00\x00\x00\x00\x01\x00",
            b"\x00\x00\x02\x80r",
            PackValues("<ifd", -10, 3.25, 0.5),
        )
    )
