import struct as Struct


# the named integer and independent handle must agree before a dimension can lose its length unit
def BindCounts(
    DataValue: bytes,
    Pairs: list[tuple[int, str, str, int, int, int, int, int]],
    Offsets: dict[str, int],
) -> dict[tuple[int, str], tuple[int, int]]:
    Result: dict[tuple[int, str], tuple[int, int]] = {}
    Ambiguous: set[tuple[int, str]] = set()
    for Owner, ParamName, Family, _, Scalar, _, Cursor, EndOffset in Pairs:
        Displacement = Offsets.get(Family)
        if Displacement is None:
            continue
        Offset = Cursor + Displacement
        if (
            Displacement < 16
            or Offset + 8 > EndOffset
            or DataValue[Offset - 16 : Offset] != Struct.pack("<4I", 8, 16, 1, 1)
        ):
            continue
        Count = Struct.unpack_from("<d", DataValue, Offset)[0]
        if not Count.is_integer() or not 0 < Count < 2**32:
            continue
        if not any(
            int.from_bytes(DataValue[Scalar : Scalar + Width], "little") == Count
            for Width in (1, 2, 4, 8)
        ):
            continue
        OwnerKey = (Owner, ParamName)
        if OwnerKey in Result:
            Ambiguous.add(OwnerKey)
        Result[OwnerKey] = (int(Count), Offset)
    return {
        OwnerKey: Value
        for OwnerKey, Value in Result.items()
        if OwnerKey not in Ambiguous
    }
