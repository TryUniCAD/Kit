import struct as Struct

# this binding exists because shared behavior needs one stable value
KMaxArchiveOffset = 4294967295


# the archive end rule is shared by writing and complete framing verification
def EncodeArcEnd(
    EndBytes: bytes,
    EntryCount: int,
    CentralSize: int,
    CentralOffset: int,
) -> bytes:
    if CentralSize > KMaxArchiveOffset:
        raise ValueError("SLDPRT directory exceeds the native size range")
    return EndBytes + Struct.pack(
        "<HHHHIIH", 0, 0, EntryCount, EntryCount, CentralSize, CentralOffset, 0
    )
