from __future__ import annotations

from dataclasses import dataclass
import struct

from convert.adapters.catia.Container import CfvTwoArchive, OsmxArchive

# this binding exists because one reader needs one attribute block tag
KAttributeTag = 0x07

# this binding exists because one reader needs one object record tag
KObjectTag = 0x05

# this binding exists because one reader needs one object header tag
KHeaderTag = 0x06

# this binding exists because one reader needs the double value tag
KDoubleTag = 0xE6

# this binding exists because one reader needs the reference three byte tag
KRefThreeTag = 0xE8

# this binding exists because one reader needs the reference four byte tag
KRefFourTag = 0xE9

# this binding exists because one reader needs the escape int tag
KEscapeTag = 0x80

# this binding exists because one reader needs the long int tag limit
KLongTagLimit = 0xE4

# this binding exists because one reader needs the terminator tag
KEndTag = 0xFE


# this definition exists because one attribute needs one decoded form
@dataclass(frozen=True, slots=True)
class AttributeValue:
    name: str
    values: tuple[str, ...]


# this definition exists because a tagged value needs one text form
def ReadValue(Stream: bytes, Cursor: int, Limit: int) -> tuple[str, int]:
    TagValue = Stream[Cursor]
    if TagValue == KDoubleTag and Cursor + 9 <= Limit:
        Value = struct.unpack_from("<d", Stream, Cursor + 1)[0]
        return (f"double:{Value:.6f}", Cursor + 9)
    if TagValue == KRefThreeTag:
        return (f"ref3:{Stream[Cursor + 1 : Cursor + 4].hex()}", Cursor + 4)
    if TagValue == KRefFourTag:
        return (f"ref4:{Stream[Cursor + 1 : Cursor + 5].hex()}", Cursor + 5)
    Packed = ReadPackInt(Stream, Cursor, Limit)
    if Packed is not None:
        Value, After = Packed
        return (f"int:{Value}", After)
    return (f"byte:{TagValue:02x}", Cursor + 1)


# this definition exists because a compact int needs one reader
def ReadPackInt(Stream: bytes, Cursor: int, Limit: int) -> tuple[int, int] | None:
    Delta = Stream[Cursor] - KEscapeTag
    if Delta == 0:
        if Cursor + 5 > Limit:
            return None
        return (struct.unpack_from("<i", Stream, Cursor + 1)[0], Cursor + 5)
    if 1 <= Delta <= 0x50:
        return (Delta - 1, Cursor + 1)
    if 0x51 <= Delta <= KLongTagLimit - KEscapeTag:
        if Cursor + 2 > Limit:
            return None
        return (((Delta - 0x51) << 8) | Stream[Cursor + 1], Cursor + 2)
    return None


# this definition exists because the record tree needs one walker
def ReadRecords(
    Stream: bytes, Start: int, Limit: int
) -> tuple[tuple[int, int, int], ...]:
    Records: list[tuple[int, int, int]] = []
    Cursor = Start
    while Cursor + 6 <= Limit:
        if Stream[Cursor] != 0x7C:
            Cursor += 1
            continue
        Length = struct.unpack_from("<I", Stream, Cursor + 2)[0]
        if Length < 6 or Cursor + Length > Limit:
            Cursor += 1
            continue
        Records.append((Stream[Cursor + 1], Cursor, Length))
        Records.extend(ReadRecords(Stream, Cursor + 6, Cursor + Length))
        Cursor += Length
    return tuple(Records)


# this definition exists because an attribute block needs one parser
def ParseAttrs(
    Stream: bytes, Start: int, Length: int, Symbols: tuple[str, ...]
) -> tuple[AttributeValue, ...]:
    Cursor = Start + 6
    Limit = Start + Length
    Header = Stream.find(b"\x7c\x06", Cursor)
    if Header >= 0:
        Limit = min(Limit, Header)
    Attributes: list[AttributeValue] = []
    while Cursor < Limit:
        if Stream[Cursor] == KEndTag:
            Cursor += 1
            continue
        KeyValue = Stream[Cursor]
        Cursor += 1
        Values: list[str] = []
        while Cursor < Limit and Stream[Cursor] != KEndTag:
            TextValue, Cursor = ReadValue(Stream, Cursor, Limit)
            Values.append(TextValue)
        if Cursor < Limit:
            Cursor += 1
        NameValue = Symbols[KeyValue] if KeyValue < len(Symbols) else f"?{KeyValue}"
        Attributes.append(AttributeValue(NameValue, tuple(Values)))
    return tuple(Attributes)


# this definition exists because one archive needs one symbol list
def ReadSymbols(Archive: CfvTwoArchive) -> tuple[str, ...]:
    Found = OsmxStream(Archive)
    if Found is None:
        return ()
    _, Parsed = Found
    return tuple(Symbol.value for Symbol in Parsed.symbols)


# this definition exists because one archive needs one osmx stream
def OsmxStream(Archive: CfvTwoArchive) -> tuple[bytes, OsmxArchive] | None:
    Folders = [Archive.outer]
    Folders.extend(Archive.nested)
    BestValue: tuple[bytes, OsmxArchive] | None = None
    for Folder in Folders:
        for StreamValue in Folder.streams:
            try:
                StreamData = Archive.stream_bytes(StreamValue, Folder)
            except (IndexError, ValueError):
                continue
            Offset = StreamData.find(b"OSMX")
            if Offset < 0:
                continue
            try:
                Parsed = OsmxArchive.from_bytes(StreamData[Offset:])
            except (IndexError, ValueError):
                continue
            if BestValue is None or len(Parsed.symbols) > len(BestValue[1].symbols):
                BestValue = (StreamData[Offset:], Parsed)
    return BestValue


# this definition exists because a part needs its attribute blocks
def AttributeValues(Archive: CfvTwoArchive) -> tuple[AttributeValue, ...]:
    Found = OsmxStream(Archive)
    if Found is None:
        return ()
    Stream, Parsed = Found
    Symbols = tuple(Symbol.value for Symbol in Parsed.symbols)
    Values: list[AttributeValue] = []
    for TagValue, Start, Length in ReadRecords(Stream, 104, Parsed.symbol_table_offset):
        if TagValue != KAttributeTag:
            continue
        Values.extend(ParseAttrs(Stream, Start, Length, Symbols))
    return tuple(Values)


# this definition exists because a relation needs its input names
def RelationNames(Archive: CfvTwoArchive) -> tuple[str, ...]:
    Names: list[str] = []
    for Formula in ReadSymbols(Archive):
        if "#In" not in Formula:
            continue
        for Piece in Formula.split("#In")[1:]:
            Token = Piece.lstrip(" :").split(",")[0].split(")")[0].split(":")[0]
            Token = Token.strip()
            if Token and Token not in Names:
                Names.append(Token)
    return tuple(Names)
