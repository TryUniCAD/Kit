from __future__ import annotations

import sys
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).parent))

from ExprValue import Encode
from GeoSwap import ReplaceGeometry
from convert.adapters.nx.PayloadBuild import ResizePayload

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmReader import ReadSplm, RebuildSplm, SplmStreams
from convert.geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.geometry.Parasolid import EncodeBrepModel
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector


def BoxBody(Length: float, Width: float, Height: float):
    Points = (
        PlaneVector(0.0, 0.0),
        PlaneVector(Length, 0.0),
        PlaneVector(Length, Width),
        PlaneVector(0.0, Width),
    )
    Lines = tuple(
        LineGeometry(Points[Index], Points[(Index + 1) % 4]) for Index in range(4)
    )
    return BuildPrism("box", Transform(), Lines, 0.0, Height)


def DimensionLanes(Payload: bytes, Old: float, New: float) -> bytes:
    if Old == New:
        return Payload
    OldHandle = Encode(Old).to_bytes(2, "little")
    NewHandle = Encode(New).to_bytes(2, "little")
    Output = bytearray(Payload)
    Cursor = 0
    while True:
        At = Output.find(b"\x00" + OldHandle + b"\x00\x00\xf0\x00", Cursor)
        if At < 0:
            break
        Output[At + 1 : At + 3] = NewHandle
        Cursor = At + 3
    OldText = repr(float(Old)).encode("ascii")
    NewText = repr(float(New)).encode("ascii")
    At = Output.find(b"p0: " + OldText)
    if At >= 0:
        Output[At + 4 : At + 4 + len(OldText)] = NewText
    return bytes(Output)


def StubFeatureSection(Payload: bytes) -> bytes:
    Info = ReadPayload(Payload)
    Bodies = [
        Payload[Section.body_offset : Section.body_offset + Section.size]
        for Section in Info.sections
    ]
    if len(Bodies) < 5:
        raise ValueError("NX payload has no feature record section to replace")
    Bodies[4] = b"OM\x01\x01"
    Resized = ResizePayload(Payload, Bodies)
    Last = ReadPayload(Resized).sections[-1]
    return Resized[: Last.body_offset + Last.size]


def AuthorBox(
    Source: bytes, Length: float, Width: float, Height: float, SourceLength: float
) -> bytes:
    Parsed = ReadSplm(Source)
    Streams = dict(SplmStreams(Parsed))
    Payload = Streams["/Root/UG_PART/UG_PART"]
    Model, Volume, AreaValue, _ = BoxBody(Length, Width, Height)
    Encoded = EncodeBrepModel(Model, PartValue=False)
    Replaced = ReplaceGeometry(Payload, Encoded)
    Replaced = DimensionLanes(Replaced, SourceLength, Length)
    Replaced = StubFeatureSection(Replaced)
    Check = ReadPayload(Replaced)
    if Check.streams[0].inflated != Encoded:
        raise AssertionError("authored geometry did not survive the payload splice")
    print(
        "authored box",
        Length,
        Width,
        Height,
        "volume",
        Volume,
        "area",
        AreaValue,
        "encoded",
        len(Encoded),
    )
    return RebuildSplm(Parsed, {"/Root/UG_PART/UG_PART": Replaced})


def Main(ArgValues: list[str]) -> int:
    if len(ArgValues) != 6:
        print(
            "usage: GeoAuthor.py <source.prt> <length> <width> <height>"
            " <source_length> <target.prt>"
        )
        return 2
    Data = AuthorBox(
        FilePath(ArgValues[0]).read_bytes(),
        float(ArgValues[1]),
        float(ArgValues[2]),
        float(ArgValues[3]),
        float(ArgValues[4]),
    )
    FilePath(ArgValues[5]).write_bytes(Data)
    print("wrote", ArgValues[5], len(Data))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
