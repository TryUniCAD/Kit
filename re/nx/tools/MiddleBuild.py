from __future__ import annotations
import sys
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).parent))
from ExprValue import Encode
from OmSection import ParseSection

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmReader import ReadSplm, SplmStreams

KNames = (
    b"\x0fEXP_lookup_exp"
    b"\x11EXP_compare_exps"
    b"\x10EXP_hash_string"
    b"\x0dEXP_hash_exp"
)
KDefault = b"\x04\x0fDefault Group\x00"


def Template(Middle: bytes) -> tuple[int, int, int, int]:
    Names = Middle.find(KNames)
    Lane = Middle.find(b"\x01\x21", Names + len(KNames))
    Default = Middle.find(KDefault, Lane)
    Records = Middle.find(b"\x00\x3f\x00\x00", Default) + 4
    return Names, Lane, Default, Records


def Flags(Count: int) -> bytes:
    if Count == 0:
        return bytes([0x02]) * 7 + bytes([0x01]) * 6
    return bytes([0x02]) * 7 + bytes([1 + Count]) * 2 + bytes([0x01]) * 7


def Head(Middle: bytes, Count: int, Id: bytes) -> bytes:
    Names = Template(Middle)[0]
    Old = bytearray(Middle[:Names])
    OldCount = Old.find(b"\x02\x13")
    Prefix = bytearray(Old[:OldCount])
    Run = 0
    while Run < len(Prefix) and Prefix[Run] == 0x02:
        Run += 1
    while Run < len(Prefix) and Prefix[Run] == 0x01:
        Run += 1
    Rest = bytes(Old[Run:])
    Head = bytearray(Flags(Count))
    Head.extend(Rest)
    Marker = Head.find(b"\x02\x13")
    Head[Marker + 2] = 9 + Count
    for Pattern in (b"\x01\x01\x01\x01\x1e\x01\x00\x01\x01\x01",):
        Position = Head.find(Pattern)
        if Position >= 0:
            Head[Position + 2] = 1 + Count
            Head[Position + 9] = 1 + Count
    Identity = Head.find(b"\xe0\x6a\xf8")
    if Identity >= 0 and Id:
        Head[Identity:Identity + len(Id)] = Id
    return bytes(Head)


def Lane(Count: int, Slots: list[tuple[int, bytes]], Classes: list[tuple[int, int]]) -> bytes:
    if Count == 0:
        return b"\x01\x21\x01\x00\x01\x11\x02\x02\x01\x02\x41"
    Occupied = {Index: Id for Index, Id in Slots}
    ClassMap = {Index: Marker for Index, Marker in Classes}
    Body = bytearray(b"\x01\x21")
    for Index in range(33):
        Body.extend(Occupied.get(Index, b"\x01"))
    Body.extend(b"\x21")
    for Index in range(32):
        Body.append(ClassMap.get(Index, 0xFF))
    Body.extend(bytes([1 + Count]) + b"\x21\x01\x00\x01\x11\x02\x02\x01\x02\x41")
    return bytes(Body)


def Default(Count: int) -> bytes:
    if Count == 0:
        return b"\x00" + KDefault + b"\x02\x02" + KDefault + b"\x00\x3f\x00\x00"
    return KDefault + KDefault + b"\x02\x02" + KDefault + b"\x00\x3f\x00\x00"


def Record(Name: bytes, Value: float, Index: int) -> bytes:
    return (
        b"\x02\x02\x04"
        + bytes([len(Name) + 2])
        + Name
        + b"\x00"
        + b"\x04\x06"
        + repr(Value).encode()
        + b"\x00"
        + b"\xff\x00\x0a"
        + bytes(10)
        + b"\x81\x00"
        + bytes([Index])
        + b"\x01\x01"
        + b"\x82\xc0\x01\x00"
        + Encode(Value).to_bytes(2, "little")
        + b"\x00\x00\x00\x00\xff"
    )


def Main(ArgValues: list[str]) -> int:
    Base = "/Users/odin/Documents/UniCAD/Kit/re/nx/oracle/"

    def Middle(Name: str) -> bytes:
        Data = FilePath(Base + Name).read_bytes()
        Streams = dict(SplmStreams(ReadSplm(Data)))
        Payload = Streams["/Root/UG_PART/UG_PART"]
        Info = ReadPayload(Payload).sections[2]
        Body = Payload[Info.body_offset : Info.body_offset + Info.size]
        return ParseSection(Body).middle

    Empty = Middle("empty.prt")
    One = Middle("empty_expr.prt")
    Built = Head(Empty, 0, b"") + KNames + b"\x00\x00" + Lane(0, [], []) + Default(0)
    print("empty", len(Built), len(Empty), Built == Empty)
    Identity = One[One.find(b"\xe0\x6a\xf8") :][:10]
    Built = (
        Head(Empty, 1, Identity)
        + KNames
        + Lane(1, [(24, bytes.fromhex("c4719778"))], [(24, 0x44)])
        + Default(1)
    )
    print("one head", len(Built), "target", len(One), Built == One[: len(Built)])
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))


def Landmarks(Middle: bytes) -> list[int]:
    Anchor = Middle.find(b"\x08SYSTEM\x00") + len(b"\x08SYSTEM\x00")
    Names = Middle.find(KNames)
    Trail = Middle.find(b"\x01\x00\x01\x11")
    Default = Middle.rfind(KDefault)
    Records = []
    Probe = Middle.find(b"\x00\x3f\x00\x00")
    while Probe >= 0:
        Probe = Middle.find(b"\x02\x02\x04", Probe + 4)
        if Probe >= 0:
            Records.append(Probe)
    return [Anchor, Anchor + 0x1B, Names - 1, Trail, Trail + 4, Default - 2, *Records]
