"""CATIA tag-difference and object-index decoders.

Recovered from CATMathStream.dll and CATGeometricObjects.dll:

- CATMathStreamImpl::ReadTagFromTagDifference at 0x1800b8670
- CATMathStreamImpl::ReadTagDifferenceAsLONG64_Scalable at 0x1800b8480
- CATMathStreamImpl::ReadULongWithSign at 0x1800a3420
- CATCGMStreamImpl::ReadRelativeTag at 0x180071da0
- CATCGMStreamImpl::ReadListOfLinkedObjects at 0x1800717f0
"""

from __future__ import annotations


def ReadTagDifference(Data: bytes, Offset: int) -> tuple[int, int, int]:
    """Decode one tag difference. Returns (Difference, IsNegative, NextOffset)."""
    Byte = Data[Offset]
    Offset += 1
    if Byte & 1:
        Difference = Byte >> 2
    else:
        Width = Byte >> 2
        if Width == 0 or Width > 8:
            raise ValueError(f"tag difference width {Width} is out of range")
        Difference = int.from_bytes(Data[Offset : Offset + Width], "little")
        Offset += Width
    return Difference, 1 if Byte & 2 else 0, Offset


def ReadTag(Data: bytes, Offset: int, Current: int) -> tuple[int, int]:
    """Decode one tag against the running tag. Returns (Tag, NextOffset)."""
    Difference, Negative, Offset = ReadTagDifference(Data, Offset)
    if Negative:
        return Current - Difference - 1, Offset
    return Current + Difference, Offset


def ReadTags(Data: bytes, Offset: int, Count: int, Current: int) -> tuple[list[int], int]:
    """Decode Count tags against the running tag."""
    Tags: list[int] = []
    for _ in range(Count):
        Current, Offset = ReadTag(Data, Offset, Current)
        Tags.append(Current)
    return Tags, Offset


def ReadRelativeTags(
    Data: bytes, Offset: int, Count: int, BaseTag: int
) -> tuple[list[int], int]:
    """Decode Count tags as BaseTag minus each stored difference."""
    Tags: list[int] = []
    for _ in range(Count):
        Difference, _, Offset = ReadTagDifference(Data, Offset)
        Tags.append(BaseTag - Difference)
    return Tags, Offset


def ReadObjectIndex(Data: bytes, Offset: int) -> tuple[int, int, int]:
    """Decode the object index varint. Returns (Index, SignFlag, NextOffset)."""
    Value = 0
    SignFlag = 0
    while True:
        Byte = Data[Offset]
        Offset += 1
        Value = (Value << 4) | (Byte & 0x0F)
        if Byte & 0x10:
            SignFlag = 1
            return Value, SignFlag, Offset
        if Offset >= len(Data):
            raise ValueError("object index varint runs past the stream")


def EncodeTagDifference(Difference: int, Negative: bool) -> bytes:
    """Encode one tag difference in the smallest form."""
    if Difference < 0x40:
        return bytes([(Difference << 2) | 1 | (2 if Negative else 0)])
    Width = max(1, (Difference.bit_length() + 7) // 8)
    if Width > 8:
        raise ValueError("tag difference does not fit in eight bytes")
    return bytes([(Width << 2) | (2 if Negative else 0)]) + Difference.to_bytes(
        Width, "little"
    )


def SelfTest() -> None:
    for Difference in (0, 1, 2, 63, 64, 255, 256, 65535, 1 << 40):
        for Negative in (False, True):
            Encoded = EncodeTagDifference(Difference, Negative)
            Decoded, IsNegative, End = ReadTagDifference(Encoded, 0)
            assert Decoded == Difference, (Difference, Decoded)
            assert bool(IsNegative) == Negative, (Negative, IsNegative)
            assert End == len(Encoded), (End, len(Encoded))
    Current = 100
    for Difference in (0, 1, 5, 63):
        for Negative in (False, True):
            Encoded = EncodeTagDifference(Difference, Negative)
            Tag, _ = ReadTag(Encoded, 0, Current)
            Expected = Current - Difference - 1 if Negative else Current + Difference
            assert Tag == Expected, (Difference, Negative, Tag, Expected)
    Tags, End = ReadTags(
        b"".join(EncodeTagDifference(Value, False) for Value in (1, 2, 3)), 0, 3, 0
    )
    assert Tags == [1, 3, 6], Tags
    Relative, End = ReadRelativeTags(
        b"".join(EncodeTagDifference(Value, False) for Value in (1, 2, 3)), 0, 3, 10
    )
    assert Relative == [9, 8, 7], Relative
    Index, SignFlag, End = ReadObjectIndex(b"\x01\x02\x13", 0)
    assert Index == 0x123, hex(Index)
    assert SignFlag == 1
    assert End == 3


if __name__ == "__main__":
    SelfTest()
    print("tag difference self-test passed")
