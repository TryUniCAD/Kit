from __future__ import annotations as Annotations

from dataclasses import dataclass as DataClass

# a registry token is a variable width integer whose prefix selects its width
KDirectCeiling = 0x80

# needed so the compact token band stays a single named boundary
KCompactCeiling = 0x90

# needed so every wide token prefix is recognised in one place
KWidePrefixes = frozenset({0x90, 0xF1} | set(range(0xA0, 0xB0)))

# needed so a null token is distinguishable from a zero value
KNullToken = 0xFF

# needed so the reference region terminator stays a single named byte
KReferenceEnd = 0x01

# needed so the class region terminator stays a single named byte
KClassEnd = 0x02

# needed so the printable name floor stays a single named boundary
KNameFloor = 0x20

# needed so the printable name ceiling stays a single named boundary
KNameCeiling = 0x7F

# needed so a runaway declaration length cannot read past the payload
KNameCeilingLength = 200


# one reference declaration names a schema and carries a raw code byte
@DataClass(frozen=True)
class ReferenceRecord:
    Offset: int
    Name: str
    Code: int


# one class declaration carries storage base fingerprint and reference tokens
@DataClass(frozen=True)
class ClassRecord:
    Offset: int
    Name: str
    Storage: int | None
    Base: int | None
    Fingerprint: bytes
    Reference: int | None


# one member declaration names a field and its storage and owner tokens
@DataClass(frozen=True)
class MemberRecord:
    Offset: int
    Name: str
    Storage: int | None
    Owner: int | None


# the three regions of a modern type registry in declaration order
@DataClass(frozen=True)
class Registry:
    References: tuple[ReferenceRecord, ...]
    Classes: tuple[ClassRecord, ...]
    Members: tuple[MemberRecord, ...]
    End: int
    Separator: int = KClassEnd


# a token decodes to a value and the cursor after it or none for a null token
def ReadToken(Payload: bytes, Cursor: int) -> tuple[int | None, int]:
    if Cursor >= len(Payload):
        raise ValueError("NX registry token runs past the payload")
    Prefix = Payload[Cursor]
    if Prefix < KDirectCeiling:
        return Prefix, Cursor + 1
    if Prefix < KCompactCeiling:
        if Cursor + 2 > len(Payload):
            raise ValueError("NX compact token runs past the payload")
        return (Prefix - KCompactCeiling + 0x10) * 256 + Payload[
            Cursor + 1
        ] + 1, Cursor + 2
    if Prefix in KWidePrefixes:
        if Cursor + 3 > len(Payload):
            raise ValueError("NX wide token runs past the payload")
        Value = (Payload[Cursor + 1] << 8) | Payload[Cursor + 2]
        return ((Prefix & 0x0F) * 65536) + Value + 1, Cursor + 3
    if Prefix == KNullToken:
        return None, Cursor + 1
    raise ValueError(f"NX registry token prefix {Prefix:#04x} is not a token")


# a declaration is a length byte a name and a body the caller consumes
def ReadName(Payload: bytes, Cursor: int) -> tuple[str, int]:
    if Cursor >= len(Payload):
        raise ValueError("NX registry declaration runs past the payload")
    Length = Payload[Cursor]
    if not 2 <= Length <= KNameCeilingLength:
        raise ValueError(f"NX registry declaration length {Length} is out of range")
    Symbols = Payload[Cursor + 1 : Cursor + Length]
    if len(Symbols) != Length - 1:
        raise ValueError("NX registry declaration name runs past the payload")
    if not all(KNameFloor <= SymbolValue < KNameCeiling for SymbolValue in Symbols):
        raise ValueError("NX registry declaration name is not printable ascii")
    return Symbols.decode("ascii"), Cursor + Length


# the reference region ends with a one byte marker and holds name code pairs
def ReadReferences(
    Payload: bytes, Cursor: int
) -> tuple[tuple[ReferenceRecord, ...], int]:
    Output: list[ReferenceRecord] = []
    while Cursor < len(Payload):
        if Payload[Cursor] == KReferenceEnd:
            return tuple(Output), Cursor + 1
        Start = Cursor
        NameValue, Cursor = ReadName(Payload, Cursor)
        if Cursor >= len(Payload):
            raise ValueError("NX reference declaration has no code byte")
        Output.append(ReferenceRecord(Start, NameValue, Payload[Cursor]))
        Cursor += 1
    raise ValueError("NX reference region has no end marker")


# the class region ends with a marker or one opaque separator before the members
def ReadClasses(
    Payload: bytes, Cursor: int
) -> tuple[tuple[ClassRecord, ...], int, int]:
    Output: list[ClassRecord] = []
    while Cursor < len(Payload):
        if Payload[Cursor] == KClassEnd:
            return tuple(Output), Cursor + 1, KClassEnd
        Start = Cursor
        try:
            NameValue, Cursor = ReadName(Payload, Cursor)
            Storage, Cursor = ReadToken(Payload, Cursor)
            BaseValue, Cursor = ReadToken(Payload, Cursor)
            Fingerprint = Payload[Cursor : Cursor + 8]
            if len(Fingerprint) != 8:
                raise ValueError("NX class declaration has no eight byte fingerprint")
            Cursor += 8
            Reference, Cursor = ReadToken(Payload, Cursor)
        except ValueError:
            return tuple(Output), Start + 1, Payload[Start]
        Output.append(
            ClassRecord(Start, NameValue, Storage, BaseValue, Fingerprint, Reference)
        )
    return tuple(Output), Cursor, KClassEnd


# the member region runs to the end of the registry and holds storage owner pairs
def ReadMembers(Payload: bytes, Cursor: int, EndValue: int) -> tuple[MemberRecord, ...]:
    Output: list[MemberRecord] = []
    while Cursor < EndValue:
        Start = Cursor
        try:
            NameValue, Cursor = ReadName(Payload, Cursor)
            Storage, Cursor = ReadToken(Payload, Cursor)
            Owner, Cursor = ReadToken(Payload, Cursor)
        except ValueError:
            break
        Output.append(MemberRecord(Start, NameValue, Storage, Owner))
    return tuple(Output)


# the registry is the reference class and member regions in that order
def ReadRegistry(Payload: bytes, Cursor: int, EndValue: int) -> Registry:
    References, Cursor = ReadReferences(Payload, Cursor)
    Classes, Cursor, Separator = ReadClasses(Payload, Cursor)
    Members = ReadMembers(Payload, Cursor, EndValue)
    return Registry(References, Classes, Members, EndValue, Separator)


# a value encodes to the shortest token that carries it
def WriteToken(Value: int | None) -> bytes:
    if Value is None:
        return bytes([KNullToken])
    if Value < KDirectCeiling:
        return bytes([Value])
    if Value <= 0x1000:
        return bytes([KCompactCeiling - 0x10 + (Value - 1) // 256, (Value - 1) % 256])
    if Value <= 0x100000:
        return bytes(
            [0xA0 | ((Value - 1) >> 16), ((Value - 1) >> 8) & 0xFF, (Value - 1) & 0xFF]
        )
    raise ValueError(f"NX registry token value {Value} is out of range")


# a declaration encodes as a length byte a name and a body the caller supplies
def WriteName(NameValue: str) -> bytes:
    Symbols = NameValue.encode("ascii")
    if not 1 <= len(Symbols) < KNameCeilingLength:
        raise ValueError(f"NX registry declaration name {NameValue!r} is out of range")
    return bytes([len(Symbols) + 1]) + Symbols


# the reference region is name code pairs followed by the end marker
def WriteReferences(References: tuple[ReferenceRecord, ...]) -> bytes:
    Output = bytearray()
    for Entry in References:
        Output += WriteName(Entry.Name)
        Output.append(Entry.Code)
    Output.append(KReferenceEnd)
    return bytes(Output)


# the class region is the four class tokens followed by the end marker
def WriteClasses(Classes: tuple[ClassRecord, ...], Separator: int = KClassEnd) -> bytes:
    Output = bytearray()
    for Entry in Classes:
        Output += WriteName(Entry.Name)
        Output += WriteToken(Entry.Storage)
        Output += WriteToken(Entry.Base)
        if len(Entry.Fingerprint) != 8:
            raise ValueError("NX class declaration needs an eight byte fingerprint")
        Output += Entry.Fingerprint
        Output += WriteToken(Entry.Reference)
    Output.append(Separator)
    return bytes(Output)


# the member region is storage owner pairs with no terminator
def WriteMembers(Members: tuple[MemberRecord, ...]) -> bytes:
    Output = bytearray()
    for Entry in Members:
        Output += WriteName(Entry.Name)
        Output += WriteToken(Entry.Storage)
        Output += WriteToken(Entry.Owner)
    return bytes(Output)


# the registry encodes as its three regions in declaration order
def WriteRegistry(RegistryValue: Registry) -> bytes:
    return (
        WriteReferences(RegistryValue.References)
        + WriteClasses(RegistryValue.Classes, RegistryValue.Separator)
        + WriteMembers(RegistryValue.Members)
    )


# the registry starts at the first declaration in the first section body
def RegistryStart(BodyValue: bytes) -> int | None:
    for Cursor in range(len(BodyValue) - 2):
        Length = BodyValue[Cursor]
        if 2 <= Length <= KNameCeilingLength and BodyValue[Cursor + 1 : Cursor + 2] == b"U":
            if BodyValue[Cursor + 2 : Cursor + 3] == b"G":
                return Cursor
    return None


# the registry extent ends where the member region stops parsing
def RegistryEnd(BodyValue: bytes, RegistryValue: Registry, Start: int) -> int:
    if not RegistryValue.Members:
        return Start + len(WriteRegistry(RegistryValue))
    Cursor = RegistryValue.Members[-1].Offset
    _, Cursor = ReadName(BodyValue, Cursor)
    _, Cursor = ReadToken(BodyValue, Cursor)
    _, Cursor = ReadToken(BodyValue, Cursor)
    return Cursor


# rewriting the registry regenerates it from the parsed records in place
def RewriteRegistry(Payload: bytes) -> bytes:
    from convert.adapters.nx.PayloadBuild import ResizePayload
    from convert.adapters.nx.PayloadReader import ReadPayload

    Parsed = ReadPayload(Payload)
    if Parsed.legacy or not Parsed.sections:
        return Payload
    Bodies = [
        Payload[Section.body_offset : Section.body_offset + Section.size]
        for Section in Parsed.sections
    ]
    First = Bodies[0]
    Start = RegistryStart(First)
    if Start is None:
        return Payload
    try:
        RegistryValue = ReadRegistry(First, Start, len(First))
    except ValueError:
        return Payload
    if not RegistryValue.Classes:
        return Payload
    EndValue = RegistryEnd(First, RegistryValue, Start)
    Bodies[0] = First[:Start] + WriteRegistry(RegistryValue) + First[EndValue:]
    return ResizePayload(Payload, Bodies)


# needed so the registry types stay a single named source for the nx adapter
__all__ = [
    "ClassRecord",
    "MemberRecord",
    "ReadRegistry",
    "ReadToken",
    "ReferenceRecord",
    "Registry",
    "RegistryEnd",
    "RegistryStart",
    "RewriteRegistry",
    "WriteClasses",
    "WriteMembers",
    "WriteName",
    "WriteReferences",
    "WriteRegistry",
    "WriteToken",
]
