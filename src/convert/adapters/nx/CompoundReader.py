from __future__ import annotations as Annotations
import struct as Struct

from convert.adapters.nx.Compound import (
    CompoundEntry,
    CompoundError,
    CompoundFile,
    CompoundStream,
)

# the free sector sentinel marks unused allocation table entries
KFreeSector = 0xFFFFFFFF

# the chain end sentinel terminates every compound sector chain
KChainEnd = 0xFFFFFFFE

# the compound signature excludes unrelated ole formats before parsing
KCompoundMagic = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

# the directory storage kind carries child streams and nested paths
KStorageKind = 1

# the directory stream kind carries one bounded byte payload
KStreamKind = 2

# the directory root kind anchors the storage tree
KRootKind = 5

# compound files cap sector size at the format maximum to bound allocations
KMaxSectorSize = 65536

# compound files cap directory entries so corrupt trees fail fast
KMaxEntryCount = 1000000


# compound parsing validates the header before following any allocation chain
def ReadCompound(DataValue: bytes) -> CompoundFile:
    if len(DataValue) < 512 or DataValue[:8] != KCompoundMagic:
        raise CompoundError("compound file signature is missing")
    SectorSize = 1 << Struct.unpack_from("<H", DataValue, 0x1E)[0]
    MiniSize = 1 << Struct.unpack_from("<H", DataValue, 0x20)[0]
    if not 128 <= SectorSize <= KMaxSectorSize:
        raise CompoundError("compound sector size is invalid")
    if not 16 <= MiniSize <= SectorSize:
        raise CompoundError("compound mini sector size is invalid")
    FatCount = Struct.unpack_from("<I", DataValue, 0x2C)[0]
    DirStart = Struct.unpack_from("<I", DataValue, 0x30)[0]
    MiniCutoff = Struct.unpack_from("<I", DataValue, 0x38)[0]
    MiniFatStart = Struct.unpack_from("<I", DataValue, 0x3C)[0]
    MiniFatCount = Struct.unpack_from("<I", DataValue, 0x40)[0]
    DifatStart = Struct.unpack_from("<I", DataValue, 0x44)[0]
    DifatCount = Struct.unpack_from("<I", DataValue, 0x48)[0]
    FatValues = ReadFatTable(DataValue, SectorSize, FatCount, DifatStart, DifatCount)
    Entries = ReadEntries(DataValue, FatValues, SectorSize, DirStart)
    if not Entries:
        raise CompoundError("compound directory is empty")
    MiniFat = ReadMiniFat(
        DataValue,
        FatValues,
        SectorSize,
        MiniFatStart,
        MiniFatCount,
    )
    MiniStream = ReadChain(
        DataValue, FatValues, SectorSize, Entries[0].start, Entries[0].size
    )
    return CompoundFile(
        DataValue,
        SectorSize,
        MiniSize,
        FatCount,
        DirStart,
        MiniCutoff,
        MiniFatStart,
        MiniFatCount,
        DifatStart,
        DifatCount,
        FatValues,
        Entries,
        MiniFat,
        MiniStream,
    )


# each sector read enforces the physical file boundary
def ReadSector(DataValue: bytes, SectorSize: int, Index: int) -> bytes:
    Start = (Index + 1) * SectorSize
    EndValue = Start + SectorSize
    if Index < 0 or EndValue > len(DataValue):
        raise CompoundError("compound sector is outside the file")
    return DataValue[Start:EndValue]


# allocation entries drive every fat and directory chain traversal
def ReadFatTable(
    DataValue: bytes,
    SectorSize: int,
    FatCount: int,
    DifatStart: int,
    DifatCount: int,
) -> tuple[int, ...]:
    Difat = [
        Struct.unpack_from("<I", DataValue, 0x4C + 4 * Index)[0] for Index in range(109)
    ]
    NextSector = DifatStart
    SeenDifat: set[int] = set()
    for _ in range(min(DifatCount, len(DataValue) // SectorSize)):
        if NextSector in (KFreeSector, KChainEnd):
            break
        if NextSector in SeenDifat:
            raise CompoundError("compound difat chain is cyclic")
        SeenDifat.add(NextSector)
        Block = ReadSector(DataValue, SectorSize, NextSector)
        Count = SectorSize // 4 - 1
        Difat.extend(
            Struct.unpack_from("<I", Block, 4 * Index)[0] for Index in range(Count)
        )
        NextSector = Struct.unpack_from("<I", Block, SectorSize - 4)[0]
    Values: list[int] = []
    for Index in Difat[:FatCount]:
        if Index in (KFreeSector, KChainEnd):
            continue
        Block = ReadSector(DataValue, SectorSize, Index)
        Values.extend(
            Struct.unpack_from("<I", Block, 4 * Offset)[0]
            for Offset in range(SectorSize // 4)
        )
    if not Values:
        raise CompoundError("compound allocation table is empty")
    return tuple(Values)


# chain traversal rejects loops and bounds every requested payload
def ReadChain(
    DataValue: bytes,
    FatTable: tuple[int, ...],
    SectorSize: int,
    Start: int,
    SizeValue: int | None = None,
) -> bytes:
    Output = bytearray()
    SeenSectors: set[int] = set()
    Index = Start
    while Index not in (KFreeSector, KChainEnd):
        if Index in SeenSectors or Index >= len(FatTable):
            raise CompoundError("compound sector chain is invalid")
        SeenSectors.add(Index)
        Output.extend(ReadSector(DataValue, SectorSize, Index))
        Index = FatTable[Index]
    if SizeValue is not None:
        if len(Output) < SizeValue:
            raise CompoundError("compound stream is shorter than declared")
        return bytes(Output[:SizeValue])
    return bytes(Output)


# mini allocation entries address the root mini stream
def ReadMiniFat(
    DataValue: bytes,
    FatTable: tuple[int, ...],
    SectorSize: int,
    Start: int,
    Count: int,
) -> tuple[int, ...]:
    if Count == 0:
        return ()
    RawValue = ReadChain(DataValue, FatTable, SectorSize, Start, Count * SectorSize)
    return tuple(
        Struct.unpack_from("<I", RawValue, 4 * Index)[0]
        for Index in range(len(RawValue) // 4)
    )


# mini chains recover small streams such as part attributes and previews
def ReadMiniChain(
    DataValue: bytes,
    MiniFatTable: tuple[int, ...],
    MiniSize: int,
    MiniStream: bytes,
    Start: int,
    SizeValue: int,
) -> bytes:
    Output = bytearray()
    SeenSectors: set[int] = set()
    Index = Start
    while Index not in (KFreeSector, KChainEnd):
        if Index in SeenSectors or Index >= len(MiniFatTable):
            raise CompoundError("compound mini chain is invalid")
        SeenSectors.add(Index)
        Begin = Index * MiniSize
        Output.extend(MiniStream[Begin : Begin + MiniSize])
        Index = MiniFatTable[Index]
    if len(Output) < SizeValue:
        raise CompoundError("compound mini stream is shorter than declared")
    return bytes(Output[:SizeValue])


# directory parsing recovers tree links before stream paths are assembled
def ReadEntries(
    DataValue: bytes, FatTable: tuple[int, ...], SectorSize: int, Start: int
) -> tuple[CompoundEntry, ...]:
    RawValue = ReadChain(DataValue, FatTable, SectorSize, Start)
    Entries: list[CompoundEntry] = []
    for Offset in range(0, len(RawValue), 128):
        Block = RawValue[Offset : Offset + 128]
        if len(Block) < 128:
            break
        Entries.append(DecodeEntry(Block, len(Entries)))
        if len(Entries) > KMaxEntryCount:
            raise CompoundError("compound directory exceeds the entry limit")
    return tuple(Entries)


# one directory block exposes names and red black tree links
def DecodeEntry(Block: bytes, Index: int) -> CompoundEntry:
    NameLength = Struct.unpack_from("<H", Block, 0x40)[0]
    if NameLength > 64:
        NameValue = ""
    else:
        NameValue = Block[: max(0, NameLength - 2)].decode("utf-16le", "replace")
    return CompoundEntry(
        Index,
        NameValue,
        Block[0x42],
        Struct.unpack_from("<I", Block, 0x44)[0],
        Struct.unpack_from("<I", Block, 0x48)[0],
        Struct.unpack_from("<I", Block, 0x4C)[0],
        Struct.unpack_from("<I", Block, 0x74)[0],
        Struct.unpack_from("<Q", Block, 0x78)[0],
    )


# one stream read chooses mini or regular storage from its declared size
def ReadStream(FileValue: CompoundFile, Entry: CompoundEntry) -> bytes:
    if Entry.kind != KStreamKind:
        raise CompoundError("compound entry is not a stream")
    if Entry.size < FileValue.mini_cutoff:
        return ReadMiniChain(
            FileValue.data,
            FileValue.minifat,
            FileValue.mini_size,
            FileValue.ministream,
            Entry.start,
            Entry.size,
        )
    return ReadChain(
        FileValue.data,
        FileValue.fat,
        FileValue.sector_size,
        Entry.start,
        Entry.size,
    )


# path collection walks the red black sibling trees without recursion limits
def ReadStreams(FileValue: CompoundFile) -> tuple[CompoundStream, ...]:
    Output: list[CompoundStream] = []
    WalkStorageMut(FileValue, FileValue.entries[0].child, "", set(), Output)
    if not Output:
        for Entry in FileValue.entries:
            if Entry.kind == KStreamKind:
                Output.append(CompoundStream(Entry.name, ReadStream(FileValue, Entry)))
    return tuple(Output)


# sibling traversal keeps storage hierarchy precise across sibling links
def WalkStorageMut(
    FileValue: CompoundFile,
    Start: int,
    Prefix: str,
    SeenEntries: set[int],
    Output: list[CompoundStream],
) -> None:
    Pending = [Start]
    while Pending:
        CurrentIndex = Pending.pop()
        if CurrentIndex in (KFreeSector, KChainEnd) or CurrentIndex in SeenEntries:
            continue
        if CurrentIndex >= len(FileValue.entries):
            raise CompoundError("compound tree points outside the directory")
        SeenEntries.add(CurrentIndex)
        Current = FileValue.entries[CurrentIndex]
        if Current.left not in (KFreeSector, KChainEnd):
            Pending.append(Current.left)
        if Current.right not in (KFreeSector, KChainEnd):
            Pending.append(Current.right)
        PathValue = Prefix + Current.name
        if Current.kind == KStreamKind:
            Output.append(CompoundStream(PathValue, ReadStream(FileValue, Current)))
        elif Current.kind in (KStorageKind, KRootKind):
            if Current.child not in (KFreeSector, KChainEnd):
                WalkStorageMut(
                    FileValue, Current.child, PathValue + "/", SeenEntries, Output
                )
