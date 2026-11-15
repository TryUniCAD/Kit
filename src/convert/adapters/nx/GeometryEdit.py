from __future__ import annotations

from dataclasses import replace as DataclassReplace
import struct as StructLib
import zlib as ZlibLib

from convert.adapters.nx.ExprValue import EncodeValue
from convert.adapters.nx.PayloadReader import ReadPayload
from convert.geometry.Parasolid import DecodeBrepMut, EncodeBrepModel
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.VectorSpace import SpaceVector

# a geometry stream starts forty five bytes after its zlib payload
KStreamHeader = 45


# needed so stream bounds keeps its nx behaviour in one reviewable place
def StreamBounds(Model: BrepModel) -> tuple[float, float, float]:
    Vertices = getattr(Model, "vertices")
    if not Vertices:
        raise ValueError("NX body length requires a body with vertices")
    XValues = [Vertex.point.x for Vertex in Vertices]
    YValues = [Vertex.point.y for Vertex in Vertices]
    ZValues = [Vertex.point.z for Vertex in Vertices]
    return (
        max(XValues) - min(XValues),
        max(YValues) - min(YValues),
        max(ZValues) - min(ZValues),
    )


# needed so scale model keeps its nx behaviour in one reviewable place
def ScaleModel(Model: BrepModel, Factor: float) -> BrepModel:

    # needed so point keeps its nx behaviour in one reviewable place
    def Point(Value: SpaceVector) -> SpaceVector:
        return SpaceVector(Value.x * Factor, Value.y, Value.z)

    Scaled: BrepModel = DataclassReplace(
        Model,
        vertices=tuple(
            DataclassReplace(Entry, point=Point(Entry.point))
            for Entry in getattr(Model, "vertices")
        ),
        surfaces=tuple(
            (
                DataclassReplace(Entry, origin=Point(Entry.origin))
                if hasattr(Entry, "origin")
                else Entry
            )
            for Entry in getattr(Model, "surfaces")
        ),
        curves=tuple(
            (
                DataclassReplace(Entry, origin=Point(Entry.origin))
                if hasattr(Entry, "origin")
                else Entry
            )
            for Entry in getattr(Model, "curves")
        ),
        edges=tuple(
            DataclassReplace(
                Entry,
                start_parameter=(
                    Entry.start_parameter * Factor
                    if Entry.start_parameter is not None
                    else None
                ),
                end_parameter=(
                    Entry.end_parameter * Factor
                    if Entry.end_parameter is not None
                    else None
                ),
            )
            for Entry in getattr(Model, "edges")
        ),
    )
    return Scaled


# needed so replace stream keeps its nx behaviour in one reviewable place
def ReplaceStream(Payload: bytes, Inflated: bytes) -> bytes:
    Parsed = ReadPayload(Payload)
    if len(Parsed.streams) != 1:
        raise ValueError("NX body length requires exactly one geometry stream")
    Stream = Parsed.streams[0]
    Start = Stream.offset - KStreamHeader
    if Start < 0 or Stream.offset + Stream.compressed > len(Payload):
        raise ValueError("NX geometry stream is outside the part payload")
    Header = bytearray(Payload[Start : Start + KStreamHeader])
    ZipValue = ZlibLib.compress(Inflated, level=1)
    StructLib.pack_into("<I", Header, 4, len(ZipValue))
    StructLib.pack_into("<I", Header, 0x0E, len(ZipValue))
    StreamEnd = Stream.offset + Stream.compressed
    Delta = len(ZipValue) - Stream.compressed
    IndexStreamEnd = Parsed.rows[1].value
    IndexRows = bytearray(Payload[:IndexStreamEnd])
    for Offset in range(0, len(IndexRows) // 12 * 12, 12):
        for Field in range(3):
            Cursor = Offset + Field * 4
            Value = StructLib.unpack_from("<I", IndexRows, Cursor)[0]
            if Value >= StreamEnd:
                StructLib.pack_into("<I", IndexRows, Cursor, Value + Delta)
    return (
        bytes(IndexRows)
        + Payload[IndexStreamEnd:Start]
        + bytes(Header)
        + ZipValue
        + Payload[StreamEnd:]
    )


# needed so format number keeps its nx behaviour in one reviewable place
def FormatNumber(Value: float) -> bytes:
    if float(Value).is_integer():
        return str(int(Value)).encode("ascii")
    return repr(float(Value)).encode("ascii")


# needed so swap dimension keeps its nx behaviour in one reviewable place
def SwapDimension(Payload: bytes, OldValue: float, NewValue: float) -> bytes:
    Marker = Payload.find(b"p0: ")
    if Marker < 0:
        raise ValueError("NX body length requires a block part with a p0 dimension")
    TokenEnd = Payload.find(b";", Marker)
    if TokenEnd < 0:
        raise ValueError("NX body length found a malformed p0 dimension")
    Token = Payload[Marker + 4 : TokenEnd]
    try:
        Current = float(Token.decode("ascii"))
    except ValueError as Error:
        raise ValueError("NX body length found a malformed p0 dimension") from Error
    if abs(Current - OldValue) > 1e-6:
        raise ValueError("NX body length requires p0 to match the measured body extent")
    OldHandle = EncodeValue(OldValue).to_bytes(2, "little")
    NewHandle = EncodeValue(NewValue).to_bytes(2, "little")
    Output = bytearray(Payload)
    Cursor = 0
    while True:
        Cursor = Output.find(b"\x00" + OldHandle + b"\x00\x00\xf0\x00", Cursor)
        if Cursor < 0:
            break
        Output[Cursor + 1 : Cursor + 3] = NewHandle
        Cursor = Cursor + 3
    NewToken = FormatNumber(NewValue)
    return bytes(Output[: Marker + 4]) + NewToken + bytes(Output[TokenEnd:])


# needed so scale body length keeps its nx behaviour in one reviewable place
def ScaleBodyLength(Payload: bytes, Length: float) -> bytes:
    if Length <= 0:
        raise ValueError("NX body length must be positive")
    Parsed = ReadPayload(Payload)
    if len(Parsed.streams) != 1:
        raise ValueError("NX body length requires exactly one geometry stream")
    Decoded = DecodeBrepMut(Parsed.streams[0].inflated)
    if Decoded is None:
        raise ValueError("NX body length requires decodable geometry")
    Model: BrepModel = Decoded
    if len(getattr(Model, "bodies")) != 1:
        raise ValueError("NX body length requires exactly one body")
    Regions = getattr(Model, "regions")
    if not Regions or not Regions[0].solid:
        raise ValueError("NX body length requires a solid body")
    Source = StreamBounds(Model)[0]
    if Source <= 0:
        raise ValueError("NX body has no measurable length")
    Scaled = ScaleModel(Model, Length / Source)
    Encoded = EncodeBrepModel(Scaled, PartValue=False)
    Replaced = ReplaceStream(Payload, Encoded)
    Replaced = SwapDimension(Replaced, Source, Length)
    Check = ReadPayload(Replaced)
    if Check.streams[0].inflated != Encoded:
        raise AssertionError("NX authored geometry did not survive the payload splice")
    return Replaced
