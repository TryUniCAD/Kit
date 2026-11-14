from __future__ import annotations

import struct
import sys
from dataclasses import replace
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).parent))

from ExprValue import Encode
from GeoSwap import ReplaceGeometry

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmReader import ReadSplm, RebuildSplm, SplmStreams
from convert.geometry.Parasolid import DecodeBrepMut, EncodeBrepModel
from interchange.geometry.models.VectorSpace import SpaceVector


def ScaleModel(Model, Factors: tuple[float, float, float]):
    X, Y, Z = Factors

    def Point(Value):
        return SpaceVector(Value.x * X, Value.y * Y, Value.z * Z)

    Vertices = [replace(Item, point=Point(Item.point)) for Item in Model.vertices]
    Surfaces = [
        replace(Item, origin=Point(Item.origin)) if hasattr(Item, "origin") else Item
        for Item in Model.surfaces
    ]
    Curves = [
        replace(Item, origin=Point(Item.origin)) if hasattr(Item, "origin") else Item
        for Item in Model.curves
    ]
    Edges = [
        replace(
            Item,
            start_parameter=(
                Item.start_parameter * X if Item.start_parameter is not None else None
            ),
            end_parameter=(
                Item.end_parameter * X if Item.end_parameter is not None else None
            ),
        )
        for Item in Model.edges
    ]
    return replace(
        Model, vertices=Vertices, surfaces=Surfaces, curves=Curves, edges=Edges
    )


def Bounds(Model) -> tuple[float, float, float]:
    Xs = [Vertex.point.x for Vertex in Model.vertices]
    Ys = [Vertex.point.y for Vertex in Model.vertices]
    Zs = [Vertex.point.z for Vertex in Model.vertices]
    return (max(Xs) - min(Xs), max(Ys) - min(Ys), max(Zs) - min(Zs))


def DimensionLanes(Payload: bytes, Old: float, New: float) -> bytes:
    if Old == New:
        return Payload
    OldHandle = Encode(Old).to_bytes(2, "little")
    NewHandle = Encode(New).to_bytes(2, "little")
    OldText = repr(float(Old)).encode()
    NewText = repr(float(New)).encode()
    Out = bytearray(Payload)
    Cursor = 0
    while True:
        At = Out.find(b"\x00" + OldHandle + b"\x00\x00\xf0\x00", Cursor)
        if At < 0:
            break
        Out[At + 1 : At + 3] = NewHandle
        Cursor = At + 3
    At = Out.find(b"p0: " + OldText)
    if At >= 0:
        Out[At + 4 : At + 4 + len(OldText)] = NewText
    return bytes(Out)


def AuthorBox(Source: bytes, Length: float) -> bytes:
    Parsed = ReadSplm(Source)
    Streams = dict(SplmStreams(Parsed))
    Payload = Streams["/Root/UG_PART/UG_PART"]
    Stream = ReadPayload(Payload).streams[0]
    Model = DecodeBrepMut(Stream.inflated)
    SourceLength = Bounds(Model)[0]
    if SourceLength <= 0:
        raise ValueError("source body has no measurable length")
    Scaled = ScaleModel(Model, (Length / SourceLength, 1.0, 1.0))
    Encoded = EncodeBrepModel(Scaled, PartValue=False)
    Replaced = ReplaceGeometry(Payload, Encoded)
    Replaced = DimensionLanes(Replaced, SourceLength, Length)
    Check = ReadPayload(Replaced)
    if Check.streams[0].inflated != Encoded:
        raise AssertionError("authored geometry did not survive the payload splice")
    print("source length", SourceLength, "authored length", Length, "encoded", len(Encoded))
    return RebuildSplm(Parsed, {"/Root/UG_PART/UG_PART": Replaced})


def Main(ArgValues: list[str]) -> int:
    if len(ArgValues) != 3:
        print("usage: GeoAuthor.py <source.prt> <length_mm> <target.prt>")
        return 2
    Data = AuthorBox(FilePath(ArgValues[0]).read_bytes(), float(ArgValues[1]))
    FilePath(ArgValues[2]).write_bytes(Data)
    print("wrote", ArgValues[2], len(Data))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
