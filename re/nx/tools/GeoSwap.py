from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).parent))

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmReader import ReadSplm, RebuildSplm, SplmStreams
from convert.geometry.Parasolid import DecodeBrepMut, EncodeBrepModel

KStreamHeader = 45


def Payload(Parsed) -> tuple[bytes, dict[str, bytes]]:
    Streams = dict(SplmStreams(Parsed))
    return Streams["/Root/UG_PART/UG_PART"], Streams


def ReplaceGeometry(Payload: bytes, Inflated: bytes) -> bytes:
    Info = ReadPayload(Payload)
    Stream = Info.streams[0]
    Start = Stream.offset - KStreamHeader
    Header = bytearray(Payload[Start : Start + KStreamHeader])
    ZipValue = zlib.compress(Inflated, level=1)
    struct.pack_into("<I", Header, 4, len(ZipValue))
    struct.pack_into("<I", Header, 0x0E, len(ZipValue))
    End = Stream.offset + Stream.compressed
    Delta = len(ZipValue) - Stream.compressed
    Tail = Payload[End:]
    Remap: dict[int, int] = {End: End + Delta}
    IndexEnd = Info.rows[1].value
    Rows = bytearray(Payload[:IndexEnd])
    for Offset in range(0, len(Rows) // 12 * 12, 12):
        for Field in range(3):
            At = Offset + Field * 4
            Value = struct.unpack_from("<I", Rows, At)[0]
            if Value >= End and Value in Remap or Value >= End:
                Value = Value + Delta
                struct.pack_into("<I", Rows, At, Value)
    return bytes(Rows) + Payload[IndexEnd:Start] + bytes(Header) + ZipValue + Tail


def Main(ArgValues: list[str]) -> int:
    if len(ArgValues) != 2:
        print("usage: GeoSwap.py <source.prt> <target.prt>")
        return 2
    Source = FilePath(ArgValues[0]).read_bytes()
    Parsed = ReadSplm(Source)
    PartData, Streams = Payload(Parsed)
    Stream = ReadPayload(PartData).streams[0]
    Model = DecodeBrepMut(Stream.inflated)
    Encoded = EncodeBrepModel(Model, PartValue=False)
    NewPayload = ReplaceGeometry(PartData, Encoded)
    Check = ReadPayload(NewPayload)
    if Check.streams[0].inflated != Encoded:
        raise AssertionError("geometry stream did not survive the payload splice")
    Out = RebuildSplm(Parsed, {"/Root/UG_PART/UG_PART": NewPayload})
    FilePath(ArgValues[1]).write_bytes(Out)
    print(
        "wrote",
        ArgValues[1],
        "bodies",
        len(Model.bodies),
        "faces",
        len(Model.faces),
        "encoded",
        len(Encoded),
        "was",
        len(Stream.inflated),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
