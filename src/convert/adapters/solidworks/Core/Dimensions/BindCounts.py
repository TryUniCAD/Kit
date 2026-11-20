import struct as Struct


# the named integer and independent handle must agree before a dimension can lose its length unit
def BindCounts(
    DataValue: bytes,
    Pairs: list[tuple[int, str, str, int, int, int, int, int]],
    Offsets: dict[str, int],
) -> dict[tuple[int, str], tuple[int, int]]:
    Result = {}
    Ambiguous = set()
    for Owner, Name, Family, _, Scalar, _, Cursor, End in Pairs:
        Displacement = Offsets.get(Family)
        if Displacement is None:
            continue
        Offset = Cursor + Displacement
        if (
            Displacement < 16
            or Offset + 8 > End
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
        Key = (Owner, Name)
        if Key in Result:
            Ambiguous.add(Key)
        Result[Key] = (int(Count), Offset)
    return {Key: Value for Key, Value in Result.items() if Key not in Ambiguous}
