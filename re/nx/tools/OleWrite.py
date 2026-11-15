"""Write an OLE2 compound file holding the streams of an NX legacy part.

The layout follows MS-CFB: 512 byte sectors, a proper mini stream for streams
below the 4096 byte cutoff, a mini FAT for those chains, and a directory with
one entry per storage and stream.
"""

from __future__ import annotations

import struct
from pathlib import Path

KFree = 0xFFFFFFFF
KEnd = 0xFFFFFFFE
KFat = 0xFFFFFFFD
KNoStream = 0xFFFFFFFF
KSector = 512
KMiniSector = 64
KCutoff = 4096


def EncodeEntry(
    Name: str,
    Kind: int,
    Left: int = KNoStream,
    Right: int = KNoStream,
    Child: int = KNoStream,
    Start: int = KEnd,
    Size: int = 0,
    Clsid: bytes = b"",
) -> bytes:
    Raw = Name.encode("utf-16-le") + b"\x00\x00"
    if len(Raw) > 64:
        raise ValueError("OLE2 directory names are limited to 31 characters")
    Entry = bytearray(128)
    Entry[0 : len(Raw)] = Raw
    struct.pack_into("<H", Entry, 0x40, len(Raw))
    Entry[0x42] = Kind
    Entry[0x43] = 1
    if Clsid:
        Entry[0x50:0x60] = Clsid
    struct.pack_into("<III", Entry, 0x44, Left, Right, Child)
    struct.pack_into("<I", Entry, 0x74, Start)
    struct.pack_into("<Q", Entry, 0x78, Size)
    return bytes(Entry)


def _Nodes(Streams: dict[tuple[str, ...], bytes]) -> list[dict[str, object]]:
    Nodes: list[dict[str, object]] = [{"name": "Root Entry", "kind": 5, "data": None}]
    Index: dict[tuple[str, ...], int] = {(): 0}
    for PathValue in Streams:
        for Depth in range(1, len(PathValue)):
            Prefix = PathValue[:Depth]
            if Prefix not in Index:
                Index[Prefix] = len(Nodes)
                Nodes.append({"name": Prefix[-1], "kind": 1, "data": None})
    for PathValue, Data in Streams.items():
        Index[PathValue] = len(Nodes)
        Nodes.append({"name": PathValue[-1], "kind": 2, "data": Data})
    Children: dict[int, list[int]] = {i: [] for i in range(len(Nodes))}
    for PathValue, Id in Index.items():
        if PathValue:
            Children[Index[PathValue[:-1]]].append(Id)
    # the directory is a red black tree; a balanced all black tree is valid
    def SortKey(Id: int) -> tuple[int, str]:
        Name = str(Nodes[Id]["name"]).upper()
        return (len(Name), Name)

    def Build(Ids: list[int]) -> int:
        if not Ids:
            return KNoStream
        Middle = len(Ids) // 2
        Node = Ids[Middle]
        Nodes[Node]["left"] = Build(Ids[:Middle])
        Nodes[Node]["right"] = Build(Ids[Middle + 1 :])
        return Node

    for Parent, Ids in Children.items():
        Nodes[Parent]["child"] = Build(sorted(Ids, key=SortKey))
    return Nodes


def WriteOle(
    Streams: dict[tuple[str, ...], bytes],
    Target: str | Path,
    RootClsid: bytes = b"",
    StorageClsids: dict[tuple[str, ...], bytes] | None = None,
) -> dict[str, int]:
    Nodes = _Nodes(Streams)
    StorageClsids = StorageClsids or {}
    for Node in Nodes:
        Node.setdefault("clsid", b"")
    for PathValue, Clsid in StorageClsids.items():
        for Node in Nodes:
            if Node["name"] == (PathValue[-1] if PathValue else "Root Entry") and Node["kind"] == 1:
                Node["clsid"] = Clsid
    if RootClsid:
        Nodes[0]["clsid"] = RootClsid

    StreamIds = [Id for Id, Node in enumerate(Nodes) if Node["kind"] == 2]
    Small = [Id for Id in StreamIds if len(Nodes[Id]["data"]) < KCutoff]
    Big = [Id for Id in StreamIds if len(Nodes[Id]["data"]) >= KCutoff]

    Mini = bytearray()
    MiniFat: list[int] = []
    for Id in Small:
        Data = Nodes[Id]["data"]
        if not Data:
            Nodes[Id]["start"] = KEnd
            Nodes[Id]["size"] = 0
            continue
        First = len(Mini) // KMiniSector
        Count = (len(Data) + KMiniSector - 1) // KMiniSector
        Nodes[Id]["start"] = First
        Nodes[Id]["size"] = len(Data)
        Mini.extend(Data)
        Mini.extend(b"\x00" * (Count * KMiniSector - len(Data)))
        for Offset in range(Count):
            MiniFat.append(First + Offset + 1 if Offset < Count - 1 else KEnd)
    MiniUsed = len(Mini)
    MiniSectors = (len(Mini) + KSector - 1) // KSector
    if Mini:
        Mini.extend(b"\x00" * (MiniSectors * KSector - len(Mini)))

    MiniFatSectors = (len(MiniFat) + KSector // 4 - 1) // (KSector // 4) if MiniFat else 0
    DirectorySectors = max(1, (len(Nodes) + 3) // 4)
    BigSectors = sum((len(Nodes[Id]["data"]) + KSector - 1) // KSector for Id in Big)
    FatSectors = 1
    while True:
        Total = FatSectors + DirectorySectors + MiniFatSectors + MiniSectors + BigSectors
        if Total <= FatSectors * (KSector // 4):
            break
        FatSectors += 1

    Fat = [KFree] * (FatSectors * (KSector // 4))
    for Index in range(FatSectors):
        Fat[Index] = KFat
    Cursor = FatSectors
    DirectoryStart = Cursor
    for Index in range(DirectorySectors):
        Fat[Cursor] = Cursor + 1 if Index < DirectorySectors - 1 else KEnd
        Cursor += 1
    MiniFatStart = Cursor if MiniFatSectors else KEnd
    for Index in range(MiniFatSectors):
        Fat[Cursor] = Cursor + 1 if Index < MiniFatSectors - 1 else KEnd
        Cursor += 1
    MiniStart = Cursor if MiniSectors else KEnd
    for Index in range(MiniSectors):
        Fat[Cursor] = Cursor + 1 if Index < MiniSectors - 1 else KEnd
        Cursor += 1
    for Id in Big:
        Data = Nodes[Id]["data"]
        Count = (len(Data) + KSector - 1) // KSector
        Nodes[Id]["start"] = Cursor
        Nodes[Id]["size"] = len(Data)
        for Index in range(Count):
            Fat[Cursor] = Cursor + 1 if Index < Count - 1 else KEnd
            Cursor += 1
    Nodes[0]["start"] = MiniStart if MiniSectors else KEnd
    Nodes[0]["size"] = MiniUsed

    Header = bytearray(KSector)
    Header[0:8] = bytes.fromhex("d0cf11e0a1b11ae1")
    struct.pack_into("<H", Header, 0x18, 0x003E)
    struct.pack_into("<H", Header, 0x1A, 0x0003)
    struct.pack_into("<H", Header, 0x1C, 0xFFFE)
    struct.pack_into("<H", Header, 0x1E, 9)
    struct.pack_into("<H", Header, 0x20, 6)
    struct.pack_into("<I", Header, 0x2C, FatSectors)
    struct.pack_into("<I", Header, 0x30, DirectoryStart)
    struct.pack_into("<I", Header, 0x38, KCutoff)
    struct.pack_into("<I", Header, 0x3C, MiniFatStart)
    struct.pack_into("<I", Header, 0x40, MiniFatSectors)
    struct.pack_into("<I", Header, 0x44, KEnd)
    struct.pack_into("<I", Header, 0x48, 0)
    Difat = [KFree] * 109
    for Index in range(FatSectors):
        Difat[Index] = Index
    struct.pack_into("<109I", Header, 0x4C, *Difat)

    Directory = bytearray(KSector * DirectorySectors)
    for Id, Node in enumerate(Nodes):
        Entry = EncodeEntry(
            str(Node["name"]),
            int(Node["kind"]),
            int(Node.get("left", KNoStream)),
            int(Node.get("right", KNoStream)),
            int(Node.get("child", KNoStream)),
            int(Node.get("start", KEnd)),
            int(Node.get("size", 0)),
            bytes(Node.get("clsid", b"")),
        )
        Directory[Id * 128 : (Id + 1) * 128] = Entry

    Body = bytearray()
    Body.extend(struct.pack("<%dI" % len(Fat), *Fat))
    Body.extend(Directory)
    if MiniFatSectors:
        Padded = MiniFat + [KFree] * (MiniFatSectors * (KSector // 4) - len(MiniFat))
        Body.extend(struct.pack("<%dI" % len(Padded), *Padded))
    Body.extend(Mini)
    for Id in Big:
        Data = Nodes[Id]["data"]
        Body.extend(Data)
        Body.extend(b"\x00" * (((len(Data) + KSector - 1) // KSector) * KSector - len(Data)))

    Path(Target).write_bytes(bytes(Header) + bytes(Body))
    return {
        "nodes": len(Nodes),
        "small": len(Small),
        "big": len(Big),
        "fat": FatSectors,
        "directory": DirectorySectors,
    }
