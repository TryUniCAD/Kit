from __future__ import annotations as Annotations
import struct as Struct

from convert.adapters.nx.Splm import (
    KAbsentFooter,
    KFooterRegion,
    KHeaderRegion,
    KMaxPathBytes,
    KMinPathBytes,
    KRootUuid,
    KSplmMagic,
    KSplmVersion,
    SplmError,
)

# offsets stay paired with sizes because directory serialization needs both
KEntryFields = tuple[str, bytes | None, int, int]


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
        ValidatePath(PathValue)
    HeaderEntries, Payload, Cursor = BuildHeaders(
        HeaderRecords,
        0x19 + DirectoryLength(HeaderRecords, KHeaderRegion) + len(HeaderTrailer),
    )
    FooterEntries, FooterEnd = BuildFootersMut(FooterData, Payload, Cursor)
    FooterOffset = FooterEnd if FooterData else KAbsentFooter
    return AssembleSplm(
        HeaderEntries,
        FooterEntries,
        Payload,
        HeaderTrailer,
        FooterOffset,
        FileTag,
        Fingerprint,
    )


# invalid paths fail early because directory offsets depend on their byte lengths
def ValidatePath(PathValue: str) -> None:
    Length = len(PathValue.encode("utf-8"))
    if (
        not PathValue.startswith("/Root")
        or not KMinPathBytes <= Length <= KMaxPathBytes
    ):
        raise SplmError("splmsstr path is invalid")


# header entries reserve payload offsets before any bytes are serialized
def BuildHeaders(
    Records: list[tuple[str, bytes | None]], Start: int
) -> tuple[list[KEntryFields], bytearray, int]:
    Entries: list[KEntryFields] = []
    Payload = bytearray()
    Cursor = Start
    for PathValue, DataValue in Records:
        SizeValue = 0 if DataValue is None else len(DataValue)
        if DataValue is not None:
            if not DataValue:
                raise SplmError("splmsstr payload must not be empty")
            Payload.extend(DataValue)
            Cursor += SizeValue
        Entries.append((PathValue, DataValue, Cursor - SizeValue, SizeValue))
    return (Entries, Payload, Cursor)


# footer entries follow the header payload and precede the footer directory
def BuildFootersMut(
    Records: list[tuple[str, bytes | None]], Payload: bytearray, Start: int
) -> tuple[list[KEntryFields], int]:
    Entries: list[KEntryFields] = []
    Cursor = Start
    for PathValue, DataValue in Records:
        SizeValue = 0 if DataValue is None else len(DataValue)
        if DataValue is not None:
            if not DataValue:
                raise SplmError("splmsstr payload must not be empty")
            Payload.extend(DataValue)
            Cursor += SizeValue
        Entries.append((PathValue, DataValue, Cursor - SizeValue, SizeValue))
    return (Entries, Cursor)


# assembly writes the header payload footer and terminal fingerprint in order
def AssembleSplm(
    HeaderEntries: list[KEntryFields],
    FooterEntries: list[KEntryFields],
    Payload: bytearray,
    HeaderTrailer: bytes,
    FooterOffset: int,
    FileTag: int,
    Fingerprint: bytes,
) -> bytes:
    Output = bytearray()
    Output.extend(KSplmMagic)
    Output.append(KSplmVersion)
    Output.extend(int(FileTag & 0xFFFFFF).to_bytes(3, "little"))
    Output.extend(b"\x00\x00\x00\x00\x00")
    Output.extend(int(FooterOffset).to_bytes(6, "little"))
    Output.extend(b"\x00\x00")
    Output.extend(WriteDirectory(HeaderEntries, KHeaderRegion))
    Output.extend(HeaderTrailer)
    Output.extend(Payload)
    if FooterEntries:
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
def WriteDirectory(Records: list[KEntryFields], Region: str) -> bytes:
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
