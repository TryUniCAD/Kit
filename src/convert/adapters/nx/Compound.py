from __future__ import annotations as Annotations
from dataclasses import dataclass as DataClass
import struct as Struct


# malformed compound files need one stable adapter owned failure
class CompoundError(ValueError):
    __slots__ = ()


# compound directory entries need identity and tree links for path recovery
@DataClass(slots=True)
class CompoundEntry:
    index: int
    name: str
    kind: int
    left: int
    right: int
    child: int
    start: int
    size: int


# compound streams need one path and exact bounded payload for native replay
@DataClass(frozen=True, slots=True)
class CompoundStream:
    path: str
    data: bytes


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


# one ole compound reader recovers nx stream paths without vendor dependencies
class CompoundFile:
    # parsing validates the complete header before any chain is followed
    def __init__(self, DataValue: bytes) -> None:
        super().__init__()
        self.data = DataValue
        if len(DataValue) < 512 or DataValue[:8] != KCompoundMagic:
            raise CompoundError("compound file signature is missing")
        self.sector_size = 1 << Struct.unpack_from("<H", DataValue, 0x1E)[0]
        self.mini_size = 1 << Struct.unpack_from("<H", DataValue, 0x20)[0]
        if not 128 <= self.sector_size <= KMaxSectorSize:
            raise CompoundError("compound sector size is invalid")
        if not 16 <= self.mini_size <= self.sector_size:
            raise CompoundError("compound mini sector size is invalid")
        self.fat_count = Struct.unpack_from("<I", DataValue, 0x2C)[0]
        self.dir_start = Struct.unpack_from("<I", DataValue, 0x30)[0]
        self.mini_cutoff = Struct.unpack_from("<I", DataValue, 0x38)[0]
        self.minifat_start = Struct.unpack_from("<I", DataValue, 0x3C)[0]
        self.minifat_count = Struct.unpack_from("<I", DataValue, 0x40)[0]
        self.difat_start = Struct.unpack_from("<I", DataValue, 0x44)[0]
        self.difat_count = Struct.unpack_from("<I", DataValue, 0x48)[0]
        self.fat = self.ReadFat()
        self.entries = self.ReadDirectory()
        self.minifat = self.ReadMiniFat()
        if not self.entries:
            raise CompoundError("compound directory is empty")
        self.ministream = self.ReadChain(self.entries[0].start, self.entries[0].size)

    # each sector read enforces the physical file boundary
    def Sector(self, Index: int) -> bytes:
        Start = (Index + 1) * self.sector_size
        EndValue = Start + self.sector_size
        if Index < 0 or EndValue > len(self.data):
            raise CompoundError("compound sector is outside the file")
        return self.data[Start:EndValue]

    # allocation entries drive every fat and directory chain traversal
    def ReadFat(self) -> tuple[int, ...]:
        Difat = [
            Struct.unpack_from("<I", self.data, 0x4C + 4 * Index)[0]
            for Index in range(109)
        ]
        NextSector = self.difat_start
        for _ in range(self.difat_count):
            if NextSector in (KFreeSector, KChainEnd):
                break
            Block = self.Sector(NextSector)
            Count = self.sector_size // 4 - 1
            Difat.extend(
                Struct.unpack_from("<I", Block, 4 * Index)[0] for Index in range(Count)
            )
            NextSector = Struct.unpack_from("<I", Block, self.sector_size - 4)[0]
        Values: list[int] = []
        for Index in Difat[: self.fat_count]:
            if Index in (KFreeSector, KChainEnd):
                continue
            Block = self.Sector(Index)
            Values.extend(
                Struct.unpack_from("<I", Block, 4 * Offset)[0]
                for Offset in range(self.sector_size // 4)
            )
        if not Values:
            raise CompoundError("compound allocation table is empty")
        return tuple(Values)

    # chain traversal rejects loops and bounds every requested payload
    def ReadChain(self, Start: int, Size: int | None = None) -> bytes:
        Output = bytearray()
        Seen: set[int] = set()
        Index = Start
        while Index not in (KFreeSector, KChainEnd):
            if Index in Seen or Index >= len(self.fat):
                raise CompoundError("compound sector chain is invalid")
            Seen.add(Index)
            Output.extend(self.Sector(Index))
            Index = self.fat[Index]
        if Size is not None:
            if len(Output) < Size:
                raise CompoundError("compound stream is shorter than declared")
            return bytes(Output[:Size])
        return bytes(Output)

    # mini allocation entries address the root mini stream
    def ReadMiniFat(self) -> tuple[int, ...]:
        if self.minifat_count == 0:
            return ()
        RawValue = self.ReadChain(
            self.minifat_start, self.minifat_count * self.sector_size
        )
        return tuple(
            Struct.unpack_from("<I", RawValue, 4 * Index)[0]
            for Index in range(len(RawValue) // 4)
        )

    # mini chains recover small streams such as part attributes and previews
    def ReadMiniChain(self, Start: int, Size: int) -> bytes:
        Output = bytearray()
        Seen: set[int] = set()
        Index = Start
        while Index not in (KFreeSector, KChainEnd):
            if Index in Seen or Index >= len(self.minifat):
                raise CompoundError("compound mini chain is invalid")
            Seen.add(Index)
            Begin = Index * self.mini_size
            Output.extend(self.ministream[Begin : Begin + self.mini_size])
            Index = self.minifat[Index]
        if len(Output) < Size:
            raise CompoundError("compound mini stream is shorter than declared")
        return bytes(Output[:Size])

    # directory parsing recovers tree links before stream paths are assembled
    def ReadDirectory(self) -> tuple[CompoundEntry, ...]:
        RawValue = self.ReadChain(self.dir_start)
        Entries: list[CompoundEntry] = []
        for Offset in range(0, len(RawValue), 128):
            Block = RawValue[Offset : Offset + 128]
            if len(Block) < 128:
                break
            NameLength = Struct.unpack_from("<H", Block, 0x40)[0]
            if NameLength > 64:
                NameValue = ""
            else:
                NameValue = Block[: max(0, NameLength - 2)].decode(
                    "utf-16le", "replace"
                )
            Entries.append(
                CompoundEntry(
                    len(Entries),
                    NameValue,
                    Block[0x42],
                    Struct.unpack_from("<I", Block, 0x44)[0],
                    Struct.unpack_from("<I", Block, 0x48)[0],
                    Struct.unpack_from("<I", Block, 0x4C)[0],
                    Struct.unpack_from("<I", Block, 0x74)[0],
                    Struct.unpack_from("<Q", Block, 0x78)[0],
                )
            )
            if len(Entries) > KMaxEntryCount:
                raise CompoundError("compound directory exceeds the entry limit")
        return tuple(Entries)

    # one stream read chooses mini or regular storage from its declared size
    def Stream(self, Entry: CompoundEntry) -> bytes:
        if Entry.kind != KStreamKind:
            raise CompoundError("compound entry is not a stream")
        if Entry.size < self.mini_cutoff:
            return self.ReadMiniChain(Entry.start, Entry.size)
        return self.ReadChain(Entry.start, Entry.size)

    # path collection walks the red black sibling trees without recursion limits
    def Streams(self) -> tuple[CompoundStream, ...]:
        Output: list[CompoundStream] = []

        # sibling traversal keeps storage hierarchy precise across sibling links
        def Walk(Index: int, Prefix: str, Seen: set[int]) -> None:
            Pending = [Index]
            while Pending:
                CurrentIndex = Pending.pop()
                if CurrentIndex in (KFreeSector, KChainEnd) or CurrentIndex in Seen:
                    continue
                if CurrentIndex >= len(self.entries):
                    raise CompoundError("compound tree points outside the directory")
                Seen.add(CurrentIndex)
                Current = self.entries[CurrentIndex]
                if Current.left not in (KFreeSector, KChainEnd):
                    Pending.append(Current.left)
                if Current.right not in (KFreeSector, KChainEnd):
                    Pending.append(Current.right)
                PathValue = Prefix + Current.name
                if Current.kind == KStreamKind:
                    Output.append(CompoundStream(PathValue, self.Stream(Current)))
                elif Current.kind in (KStorageKind, KRootKind):
                    if Current.child not in (KFreeSector, KChainEnd):
                        Walk(Current.child, PathValue + "/", Seen)

        Walk(self.entries[0].child, "", set())
        if not Output:
            for Entry in self.entries:
                if Entry.kind == KStreamKind:
                    Output.append(CompoundStream(Entry.name, self.Stream(Entry)))
        return tuple(Output)
