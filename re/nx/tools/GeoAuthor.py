from __future__ import annotations

import struct
import sys
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).parent))

from ExprValue import Encode
from GeoSwap import ReplaceGeometry

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
    Lines = tuple(LineGeometry(Points[Index], Points[(Index + 1) % 4]) for Index in range(4))
    Model, Volume, AreaValue, Bounds = BuildPrism("body", Transform(), Lines, 0.0, Height)
    return Model, Volume, AreaValue


def DimensionLanes(Payload: bytes, Old: float, New: float) -> bytes:
    OldHandle = Encode(Old).to_bytes(2, "little")
    NewHandle = Encode(New).to_bytes(2, "little")
    OldText = repr(float(Old))
    NewText = repr(float(New))
    Out = bytearray(Payload)
    # the feature dimension table stores the same handle next to a marker
    Cursor = 0
    while True:
        At = Out.find(b"\x00" + OldHandle + b"\x00\x00\xf0\x00", Cursor)
        if At < 0:
            break
        Out[At + 1 : At + 3] = NewHandle
        Cursor = At + 3
    # the feature dimension also carries the resolved text of the dimension
    At = Out.find(b"p0: " + OldText.encode())
    if At >= 0:
        Out[At + 4 : At + 4 + len(OldText)] = NewText.encode()
    return bytes(Out)


def AuthorBox(Source: bytes, Length: float, Width: float, Height: float) -> bytes:
    Parsed = ReadSplm(Source)
    Streams = dict(SplmStreams(Parsed))
    Payload = Streams["/Root/UG_PART/UG_PART"]
    Model, Volume, AreaValue = BoxBody(Length, Width, Height)
    Encoded = EncodeBrepModel(Model, PartValue=False)
    Replaced = ReplaceGeometry(Payload, Encoded)
    Replaced = DimensionLanes(Replaced, 40.0, Length)
    Check = ReadPayload(Replaced)
    if Check.streams[0].inflated != Encoded:
        raise AssertionError("authored geometry did not survive the payload splice")
    print("model volume", Volume, "area", AreaValue, "encoded", len(Encoded))
    return RebuildSplm(Parsed, {"/Root/UG_PART/UG_PART": Replaced})


def Main(ArgValues: list[str]) -> int:
    if len(ArgValues) != 5:
        print("usage: GeoAuthor.py <source.prt> <length> <width> <height> <target.prt>")
        return 2
    Data = AuthorBox(
        FilePath(ArgValues[0]).read_bytes(),
        float(ArgValues[1]),
        float(ArgValues[2]),
        float(ArgValues[3]),
    )
    FilePath(ArgValues[4]).write_bytes(Data)
    print("wrote", ArgValues[4], len(Data))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
