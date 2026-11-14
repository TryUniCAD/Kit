from __future__ import annotations as Annotations
from dataclasses import dataclass as DataClass
import struct as Struct


# modern nx container errors stay distinct from malformed object payloads
class SplmError(ValueError):
    __slots__ = ()


# the modern nx signature identifies splmsstr before directory parsing
KSplmMagic = b"SPLMSSTR"

# the supported splmsstr layout version remains six across observed nx releases
KSplmVersion = 6

# the absent footer offset states that the header directory is complete
KAbsentFooter = 0xFFFFFFFFFFFF

# the root storage uuid is stable across nx saved parts
KRootUuid = bytes.fromhex("611ec9b3fa60d1118ad90800362fb302")

# header entries name paths before the payload section
KHeaderRegion = "HEADER"

# footer entries carry the saved toggle information near end of file
KFooterRegion = "FOOTER"

# path lengths remain bounded by the splmsstr directory grammar
KMinPathBytes = 6

# path lengths remain bounded by the splmsstr directory grammar
KMaxPathBytes = 128


# one directory entry preserves the path payload and region for exact replay
@DataClass(frozen=True, slots=True)
class SplmEntry:
    path: str
    region: str
    data: bytes | None
    offset: int
    size: int


# the parsed splmsstr container exposes streams and rebuild metadata
class SplmFile:
    # parsing keeps directory ordering because nx may depend on it
    def __init__(self, DataValue: bytes) -> None:
        super().__init__()
        self.data = DataValue
        if len(DataValue) < 0x1F or DataValue[:8] != KSplmMagic:
            raise SplmError("splmsstr signature is missing")
        self.version = DataValue[8]
        if self.version != KSplmVersion:
            raise SplmError("splmsstr version is unsupported")
        self.file_tag = int.from_bytes(DataValue[9:12], "little")
        self.footer_offset = int.from_bytes(DataValue[0x11:0x17], "little")
        self.entries = list(self.ReadRegion(0x19, KHeaderRegion))
        self.fingerprint = b""
        if self.footer_offset != KAbsentFooter:
            if self.footer_offset + 10 > len(DataValue):
                raise SplmError("splmsstr footer offset is outside the file")
            self.entries.extend(self.ReadRegion(self.footer_offset, KFooterRegion))
            self.fingerprint = DataValue[-4:]
        self.entries = tuple(self.entries)
        self.header_trailer = self.HeaderTrailer()

    # header padding preserves nx reserved metadata between directory and payload
    def HeaderTrailer(self) -> bytes:
        HeaderEnd = 0x19 + DirectoryLength(
            [
                (Entry.path, None)
                for Entry in self.entries
                if Entry.region == KHeaderRegion
            ],
            KHeaderRegion,
        )
        Offsets = [
            Entry.offset
            for Entry in self.entries
            if Entry.region == KHeaderRegion and Entry.size
        ]
        if not Offsets or min(Offsets) < HeaderEnd:
            return b""
        return self.data[HeaderEnd : min(Offsets)]

    # each region validates its marker count and complete entry framing
    def ReadRegion(self, Offset: int, Region: str) -> tuple[SplmEntry, ...]:
        Marker = Region.encode("ascii")
        if self.data[Offset : Offset + 6] != Marker:
            raise SplmError(f"splmsstr {Region.lower()} marker is missing")
        Count = Struct.unpack_from("<I", self.data, Offset + 6)[0]
        Position = Offset + 10
        Entries: list[SplmEntry] = []
        for _ in range(Count):
            if Position + 4 > len(self.data):
                raise SplmError("splmsstr entry length is truncated")
            NameLength = Struct.unpack_from("<I", self.data, Position)[0]
            Position += 4
            if not KMinPathBytes <= NameLength <= KMaxPathBytes:
                raise SplmError("splmsstr entry path length is invalid")
            EndValue = Position + NameLength
            if EndValue + 16 > len(self.data):
                raise SplmError("splmsstr entry is truncated")
            try:
                PathValue = self.data[Position:EndValue].decode("utf-8")
            except UnicodeDecodeError as ErrorInfo:
                raise SplmError("splmsstr entry path is not utf-8") from ErrorInfo
            Position = EndValue
            Payload = self.data[Position : Position + 16]
            Position += 16
            if not PathValue.startswith("/Root"):
                raise SplmError("splmsstr entry path is outside root")
            if PathValue == "/Root/":
                OffsetValue = 0
                SizeValue = 0
            else:
                OffsetValue = Struct.unpack_from("<Q", Payload, 0)[0]
                SizeValue = Struct.unpack_from("<Q", Payload, 8)[0]
            if SizeValue:
                if OffsetValue + SizeValue > len(self.data):
                    raise SplmError("splmsstr entry payload is outside the file")
                if (
                    self.footer_offset != KAbsentFooter
                    and OffsetValue + SizeValue > self.footer_offset
                ):
                    raise SplmError("splmsstr payload crosses the footer")
            Entries.append(SplmEntry(PathValue, Region, None, OffsetValue, SizeValue))
        return tuple(Entries)

    # stream lookup returns the exact bounded payload for native parsing
    def Stream(self, PathValue: str) -> bytes | None:
        for Entry in self.entries:
            if Entry.path == PathValue and Entry.size:
                return self.data[Entry.offset : Entry.offset + Entry.size]
        return None

    # stream inventory preserves directory order and sizes for diagnostics
    def Streams(self) -> tuple[tuple[str, bytes], ...]:
        return tuple(
            (
                (Entry.path, self.data[Entry.offset : Entry.offset + Entry.size])
                for Entry in self.entries
                if Entry.size
            )
        )

    # rebuilding recomputes every offset while retaining directory semantics
    def Rebuild(self, Overrides: dict[str, bytes] | None = None) -> bytes:
        Replacements = {
            (
                PathValue if PathValue.startswith("/Root/") else "/Root/" + PathValue
            ): Value
            for PathValue, Value in (Overrides or {}).items()
        }
        HeaderData: list[tuple[str, bytes | None]] = []
        FooterData: list[tuple[str, bytes | None]] = []
        for Entry in self.entries:
            if Entry.path == "/Root/":
                Target = HeaderData
                Payload = None
            elif Entry.size:
                Payload = Replacements.get(
                    Entry.path,
                    self.data[Entry.offset : Entry.offset + Entry.size],
                )
                Target = FooterData if Entry.region == KFooterRegion else HeaderData
            else:
                Payload = None
                Target = FooterData if Entry.region == KFooterRegion else HeaderData
            if not any(PathValue == Entry.path for PathValue, _ in Target):
                Target.append((Entry.path, Payload))
        return BuildSplm(
            HeaderData,
            FooterData,
            FileTag=self.file_tag,
            Fingerprint=self.fingerprint,
            HeaderTrailer=self.header_trailer,
        )


# building creates a complete modern container from named payloads alone
def BuildSplm(
    HeaderRecords: list[tuple[str, bytes | None]],
    FooterRecords: list[tuple[str, bytes | None]] | None = None,
    *,
    FileTag: int = 0,
    Fingerprint: bytes = b"",
    HeaderTrailer: bytes = b"",
) -> bytes:
    FooterData = list(FooterRecords or ())
    Paths = [PathValue for PathValue, _ in HeaderRecords + FooterData]
    if len(Paths) != len(set(Paths)):
        raise SplmError("splmsstr paths must be unique")
    for PathValue in Paths:
        if (
            not PathValue.startswith("/Root")
            or not KMinPathBytes <= len(PathValue.encode("utf-8")) <= KMaxPathBytes
        ):
            raise SplmError("splmsstr path is invalid")
    HeaderLength = DirectoryLength(HeaderRecords, KHeaderRegion)
    PayloadOffset = 0x19 + HeaderLength + len(HeaderTrailer)
    HeaderEntries: list[tuple[str, bytes | None, int, int]] = []
    Payloads = bytearray()
    Cursor = PayloadOffset
    for PathValue, DataValue in HeaderRecords:
        SizeValue = 0 if DataValue is None else len(DataValue)
        if DataValue is not None:
            if not DataValue:
                raise SplmError("splmsstr payload must not be empty")
            Payloads.extend(DataValue)
            Cursor += SizeValue
        HeaderEntries.append((PathValue, DataValue, Cursor - SizeValue, SizeValue))
    FooterEntries: list[tuple[str, bytes | None, int, int]] = []
    for PathValue, DataValue in FooterData:
        SizeValue = 0 if DataValue is None else len(DataValue)
        if DataValue is not None:
            if not DataValue:
                raise SplmError("splmsstr payload must not be empty")
            Payloads.extend(DataValue)
            Cursor += SizeValue
        FooterEntries.append((PathValue, DataValue, Cursor - SizeValue, SizeValue))
    FooterOffset = Cursor if FooterData else KAbsentFooter
    Output = bytearray()
    Output.extend(KSplmMagic)
    Output.append(KSplmVersion)
    Output.extend(int(FileTag & 0xFFFFFF).to_bytes(3, "little"))
    Output.extend(b"\x00\x00\x00\x00\x00")
    Output.extend(int(FooterOffset).to_bytes(6, "little"))
    Output.extend(b"\x00\x00")
    Output.extend(WriteDirectory(HeaderEntries, KHeaderRegion))
    Output.extend(HeaderTrailer)
    Output.extend(Payloads)
    if FooterData:
        Output.extend(WriteDirectory(FooterEntries, KFooterRegion))
        Output.extend(Fingerprint[:4].ljust(4, b"\x00"))
    return bytes(Output)


# directory length fixes the payload start before offsets are serialized
def DirectoryLength(Records: list[tuple[str, bytes | None]], Region: str) -> int:
    Total = 6 + 4
    for PathValue, _ in Records:
        Total += 4 + len(PathValue.encode("utf-8")) + 16
    return Total


# directory serialization writes root identity and exact entry payloads
def WriteDirectory(
    Records: list[tuple[str, bytes | None, int, int]], Region: str
) -> bytes:
    Output = bytearray(Region.encode("ascii"))
    Output.extend(Struct.pack("<I", len(Records)))
    for PathValue, DataValue, OffsetValue, SizeValue in Records:
        Encoded = PathValue.encode("utf-8")
        Output.extend(Struct.pack("<I", len(Encoded)))
        Output.extend(Encoded)
        if PathValue == "/Root/":
            Output.extend(KRootUuid)
        elif DataValue is None:
            Output.extend(b"\x00" * 16)
        else:
            Output.extend(Struct.pack("<QQ", OffsetValue, SizeValue))
    return bytes(Output)
