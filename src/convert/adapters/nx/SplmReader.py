from __future__ import annotations as Annotations
import struct as Struct

from convert.adapters.nx.Splm import (
    KAbsentFooter,
    KFooterRegion,
    KHeaderRegion,
    KMaxPathBytes,
    KMinPathBytes,
    KSplmMagic,
    KSplmVersion,
    SplmEntry,
    SplmError,
    SplmFile,
)
from convert.adapters.nx.SplmBuild import BuildSplm, DirectoryLength


# parsing keeps directory ordering because nx may depend on it
def ReadSplm(DataValue: bytes) -> SplmFile:
    if len(DataValue) < 0x1F or DataValue[:8] != KSplmMagic:
        raise SplmError("splmsstr signature is missing")
    Version = DataValue[8]
    if Version != KSplmVersion:
        raise SplmError("splmsstr version is unsupported")
    FileTag = int.from_bytes(DataValue[9:12], "little")
    FooterOffset = int.from_bytes(DataValue[0x11:0x17], "little")
    Entries = list(ReadSplmRegion(DataValue, 0x19, KHeaderRegion, FooterOffset))
    Fingerprint = b""
    if FooterOffset != KAbsentFooter:
        if FooterOffset + 10 > len(DataValue):
            raise SplmError("splmsstr footer offset is outside the file")
        Entries.extend(
            ReadSplmRegion(DataValue, FooterOffset, KFooterRegion, FooterOffset)
        )
        Fingerprint = DataValue[-4:]
    FileValue = SplmFile(
        DataValue,
        Version,
        FileTag,
        FooterOffset,
        tuple(Entries),
        Fingerprint,
        b"",
    )
    return SplmFile(
        DataValue,
        Version,
        FileTag,
        FooterOffset,
        tuple(Entries),
        Fingerprint,
        ReadTrailer(FileValue),
    )


# each region validates its marker count and complete entry framing
def ReadSplmRegion(
    DataValue: bytes, Offset: int, Region: str, FooterOffset: int
) -> tuple[SplmEntry, ...]:
    Marker = Region.encode("ascii")
    if DataValue[Offset : Offset + 6] != Marker:
        raise SplmError(f"splmsstr {Region.lower()} marker is missing")
    Count = Struct.unpack_from("<I", DataValue, Offset + 6)[0]
    Position = Offset + 10
    Entries: list[SplmEntry] = []
    for _ in range(Count):
        Entry, Position = ReadSplmEntry(DataValue, Position, Region, FooterOffset)
        Entries.append(Entry)
    return tuple(Entries)


# one directory entry validates path length payload bounds and footer crossing
def ReadSplmEntry(
    DataValue: bytes, Position: int, Region: str, FooterOffset: int
) -> tuple[SplmEntry, int]:
    if Position + 4 > len(DataValue):
        raise SplmError("splmsstr entry length is truncated")
    NameLength = Struct.unpack_from("<I", DataValue, Position)[0]
    Position += 4
    if not KMinPathBytes <= NameLength <= KMaxPathBytes:
        raise SplmError("splmsstr entry path length is invalid")
    EndValue = Position + NameLength
    if EndValue + 16 > len(DataValue):
        raise SplmError("splmsstr entry is truncated")
    try:
        PathValue = DataValue[Position:EndValue].decode("utf-8")
    except UnicodeDecodeError as ErrorInfo:
        raise SplmError("splmsstr entry path is not utf-8") from ErrorInfo
    Position = EndValue
    Payload = DataValue[Position : Position + 16]
    Position += 16
    if not PathValue.startswith("/Root"):
        raise SplmError("splmsstr entry path is outside root")
    OffsetValue = 0
    SizeValue = 0
    if PathValue != "/Root/":
        OffsetValue = Struct.unpack_from("<Q", Payload, 0)[0]
        SizeValue = Struct.unpack_from("<Q", Payload, 8)[0]
    if SizeValue:
        if OffsetValue + SizeValue > len(DataValue):
            raise SplmError("splmsstr entry payload is outside the file")
        if FooterOffset != KAbsentFooter and OffsetValue + SizeValue > FooterOffset:
            raise SplmError("splmsstr payload crosses the footer")
    return (SplmEntry(PathValue, Region, None, OffsetValue, SizeValue), Position)


# header padding preserves nx reserved metadata between directory and payload
def ReadTrailer(FileValue: SplmFile) -> bytes:
    HeaderRecords: list[tuple[str, bytes | None]] = [
        (Entry.path, None)
        for Entry in FileValue.entries
        if Entry.region == KHeaderRegion
    ]
    HeaderEnd = 0x19 + DirectoryLength(HeaderRecords, KHeaderRegion)
    Offsets = [
        Entry.offset
        for Entry in FileValue.entries
        if Entry.region == KHeaderRegion and Entry.size
    ]
    if not Offsets or min(Offsets) < HeaderEnd:
        return b""
    return FileValue.data[HeaderEnd : min(Offsets)]


# stream lookup returns the exact bounded payload for native parsing
def SplmStream(FileValue: SplmFile, PathValue: str) -> bytes | None:
    for Entry in FileValue.entries:
        if Entry.path == PathValue and Entry.size:
            return FileValue.data[Entry.offset : Entry.offset + Entry.size]
    return None


# stream inventory preserves directory order and sizes for diagnostics
def SplmStreams(FileValue: SplmFile) -> tuple[tuple[str, bytes], ...]:
    return tuple(
        (
            (
                Entry.path,
                FileValue.data[Entry.offset : Entry.offset + Entry.size],
            )
            for Entry in FileValue.entries
            if Entry.size
        )
    )


# rebuilding recomputes every offset while retaining directory semantics
def RebuildSplm(
    FileValue: SplmFile, Overrides: dict[str, bytes] | None = None
) -> bytes:
    Replacements = ReplacementMap(Overrides)
    HeaderData: list[tuple[str, bytes | None]] = []
    FooterData: list[tuple[str, bytes | None]] = []
    for Entry in FileValue.entries:
        Payload = None
        if Entry.size:
            Payload = Replacements.get(
                Entry.path,
                FileValue.data[Entry.offset : Entry.offset + Entry.size],
            )
        Target = FooterData if Entry.region == KFooterRegion else HeaderData
        if not any(PathValue == Entry.path for PathValue, _ in Target):
            Target.append((Entry.path, Payload))
    return BuildSplm(
        HeaderData,
        FooterData,
        FileTag=FileValue.file_tag,
        Fingerprint=FileValue.fingerprint,
        HeaderTrailer=FileValue.header_trailer,
    )


# override keys accept both root relative and absolute stream names
def ReplacementMap(Overrides: dict[str, bytes] | None) -> dict[str, bytes]:
    return {
        (PathValue if PathValue.startswith("/Root/") else "/Root/" + PathValue): Value
        for PathValue, Value in (Overrides or {}).items()
    }
