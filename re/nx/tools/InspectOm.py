from __future__ import annotations
import struct
import sys
from pathlib import Path

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmReader import ReadSplm, SplmStreams


def Main(ArgValues: list[str]) -> int:
    if len(ArgValues) != 1:
        print("usage: InspectOm.py <part.prt>")
        return 2
    DataValue = Path(ArgValues[0]).read_bytes()
    Parsed = ReadSplm(DataValue)
    Streams = dict(SplmStreams(Parsed))
    PartData = Streams["/Root/UG_PART/UG_PART"]
    Payload = ReadPayload(PartData)
    print("rows", len(Payload.rows), "sections", len(Payload.sections))
    for Index, Section in enumerate(Payload.sections):
        Body = PartData[Section.body_offset : Section.body_offset + Section.size]
        Flags = Body[0x0C:0x10]
        Stamp = struct.unpack_from("<I", Body, 0x10)[0]
        CountA = struct.unpack_from("<I", Body, 0x32)[0]
        CountB = struct.unpack_from("<I", Body, 0x36)[0]
        CountC = struct.unpack_from("<I", Body, 0x3E)[0]
        Pointer = struct.unpack_from("<I", Body, 0x52)[0]
        Names = []
        Position = 0x56
        while len(Names) < 12 and Position + 2 <= len(Body):
            Length = Body[Position + 1]
            Start = Position + 2
            End = Start + Length
            if Length < 2 or End > len(Body):
                break
            Text = Body[Start:End].rstrip(b"\0")
            if not Text or not all(32 <= Item < 127 for Item in Text):
                break
            Names.append(Text.decode("ascii"))
            Position = End + (11 if Body[Position] == 1 else 0)
        print(
            "section",
            Index,
            "size",
            Section.size,
            "flags",
            Flags.hex(),
            "stamp",
            hex(Stamp),
            "counts",
            CountA,
            CountB,
            CountC,
            "pointer",
            hex(Pointer),
            "names",
            Names,
            "next",
            hex(Position),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
