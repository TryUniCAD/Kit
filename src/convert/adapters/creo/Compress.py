from __future__ import annotations

from convert.adapters.creo.CreoFormat import CreoFormat

KMaxSectionBytes = 64 * 1024 * 1024
KMaxCodes = 1 << 17


def SkipGroup(
    Position: int,
    BitBuffer: int,
    BitCount: int,
    GroupCount: int,
    CodeSize: int,
    DataValue: bytes,
) -> tuple[int, int, int]:
    Remainder = (8 - GroupCount % 8) % 8
    SkipBits = Remainder * CodeSize
    while SkipBits > 0:
        if BitCount == 0:
            if Position >= len(DataValue):
                return (Position, BitBuffer, BitCount)
            BitBuffer = DataValue[Position]
            Position += 1
            BitCount = 8
        Taken = min(SkipBits, BitCount)
        BitBuffer >>= Taken
        BitCount -= Taken
        SkipBits -= Taken
    return (Position, BitBuffer, BitCount)


def ReadBits(
    DataValue: bytes, Position: int, BitBuffer: int, BitCount: int, CodeSize: int
) -> tuple[int, int, int, bool]:
    while BitCount < CodeSize:
        if Position >= len(DataValue):
            return (Position, BitBuffer, BitCount, False)
        BitBuffer |= DataValue[Position] << BitCount
        Position += 1
        BitCount += 8
    return (Position, BitBuffer, BitCount, True)


def SelectCode(
    CodeValue: int, TableSize: int, Previous: int | None
) -> tuple[int, bool]:
    if Previous is None:
        if CodeValue >= TableSize:
            raise CreoFormat("Creo compression first code is invalid")
        return (CodeValue, False)
    if CodeValue < TableSize:
        return (CodeValue, False)
    if CodeValue == TableSize:
        return (Previous, True)
    raise CreoFormat("Creo compression code is outside the table")


def ExpandCode(
    Prefixes: list[int], LastBytes: list[int], EntryCode: int
) -> tuple[bytearray, int]:
    Stack = bytearray()
    Cursor = EntryCode
    Guard = 0
    while True:
        if Cursor >= len(Prefixes) or Cursor >= len(LastBytes):
            raise CreoFormat("Creo compression prefix is invalid")
        Stack.append(LastBytes[Cursor])
        if Cursor < 256:
            break
        Cursor = Prefixes[Cursor]
        Guard += 1
        if Guard > KMaxCodes:
            raise CreoFormat("Creo compression dictionary loops")
    FirstByte = Stack[-1] if Stack else 0
    return (Stack, FirstByte)


def UpdateDictMut(
    Prefixes: list[int],
    LastBytes: list[int],
    Previous: int | None,
    FirstByte: int,
    MaxBits: int,
) -> None:
    if Previous is not None and len(Prefixes) < (1 << MaxBits):
        Prefixes.append(Previous)
        LastBytes.append(FirstByte)


def ResetBlockMut(
    Prefixes: list[int],
    LastBytes: list[int],
    Position: int,
    BitBuffer: int,
    BitCount: int,
    GroupCount: int,
    CodeSize: int,
    DataValue: bytes,
) -> tuple[int, int, int]:
    del Prefixes[257:]
    del LastBytes[257:]
    return SkipGroup(Position, BitBuffer, BitCount, GroupCount, CodeSize, DataValue)


def InitState(Flags: int) -> tuple[int, bool, list[int], list[int]]:
    MaxBits = Flags & 0x1F
    if MaxBits < 9 or MaxBits > 16:
        raise CreoFormat("Creo compression code width is invalid")
    BlockMode = bool(Flags & 0x80)
    Prefixes = list(range(256))
    LastBytes = list(range(256))
    if BlockMode:
        Prefixes.append(0)
        LastBytes.append(0)
    return (MaxBits, BlockMode, Prefixes, LastBytes)


def DecodeCodeMut(
    CodeValue: int,
    Prefixes: list[int],
    LastBytes: list[int],
    Previous: int | None,
    MaxBits: int,
    Output: bytearray,
    Limit: int,
) -> int | None:
    EntryCode, AddFirst = SelectCode(CodeValue, len(Prefixes), Previous)
    Stack, FirstByte = ExpandCode(Prefixes, LastBytes, EntryCode)
    if len(Output) + len(Stack) + int(AddFirst) > Limit:
        raise CreoFormat("Creo compression output exceeds its declaration")
    Output.extend(reversed(Stack))
    if AddFirst:
        Output.append(FirstByte)
    UpdateDictMut(Prefixes, LastBytes, Previous, FirstByte, MaxBits)
    return min(CodeValue, len(Prefixes) - 1)


def GrowCode(
    Prefixes: list[int],
    Position: int,
    BitBuffer: int,
    BitCount: int,
    GroupCount: int,
    CodeSize: int,
    MaxBits: int,
    DataValue: bytes,
) -> tuple[int, int, int, int, int]:
    if len(Prefixes) >= (1 << CodeSize) and CodeSize < MaxBits:
        Position, BitBuffer, BitCount = SkipGroup(
            Position, BitBuffer, BitCount, GroupCount, CodeSize, DataValue
        )
        CodeSize += 1
        GroupCount = 0
    return (Position, BitBuffer, BitCount, CodeSize, GroupCount)


def Uncompress(DataValue: bytes, Expected: int) -> bytes:
    if len(DataValue) < 4 or DataValue[:2] != b"\x1f\x9d":
        raise CreoFormat("Creo section is not Unix-compressed")
    MaxBits, BlockMode, Prefixes, LastBytes = InitState(DataValue[2])
    Limit = min(max(Expected, 1), KMaxSectionBytes)
    Position = 3
    BitBuffer = 0
    BitCount = 0
    CodeSize = 9
    GroupCount = 0
    Previous: int | None = None
    Output = bytearray()
    while len(Output) < Limit:
        Position, BitBuffer, BitCount, HasBits = ReadBits(
            DataValue, Position, BitBuffer, BitCount, CodeSize
        )
        if not HasBits:
            return bytes(Output)
        CodeValue = BitBuffer & ((1 << CodeSize) - 1)
        BitBuffer >>= CodeSize
        BitCount -= CodeSize
        GroupCount += 1
        if BlockMode and CodeValue == 256:
            Position, BitBuffer, BitCount = ResetBlockMut(
                Prefixes,
                LastBytes,
                Position,
                BitBuffer,
                BitCount,
                GroupCount,
                CodeSize,
                DataValue,
            )
            CodeSize = 9
            GroupCount = 0
            Previous = None
            continue
        Previous = DecodeCodeMut(
            CodeValue, Prefixes, LastBytes, Previous, MaxBits, Output, Limit
        )
        Position, BitBuffer, BitCount, CodeSize, GroupCount = GrowCode(
            Prefixes,
            Position,
            BitBuffer,
            BitCount,
            GroupCount,
            CodeSize,
            MaxBits,
            DataValue,
        )
    return bytes(Output)
