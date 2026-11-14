from __future__ import annotations
import sys
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).parent))
from AuthorName import SplicePayload
from ExprValue import Encode
from OmSection import BuildSection, ParseSection, Section

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmReader import ReadSplm, SplmStreams, RebuildSplm


def Rewrite(Template: bytes, Name: bytes, Value: float) -> bytes:
    Parsed = ReadSplm(Template)
    Streams = dict(SplmStreams(Parsed))
    Payload = Streams["/Root/UG_PART/UG_PART"]
    Info = ReadPayload(Payload).sections
    Bodies = []
    for Index, Entry in enumerate(Info):
        Body = Payload[Entry.body_offset : Entry.body_offset + Entry.size]
        SectionValue = ParseSection(Body)
        Middle = bytearray(SectionValue.middle)
        Marker = Middle.find(b"kit_len")
        if Marker < 0:
            Bodies.append(BuildSection(SectionValue))
            continue
        Length = Middle[Marker - 1]
        OldText = Middle[Marker : Marker + (Length - 2)]
        Middle[Marker : Marker + len(OldText)] = Name
        Middle[Marker - 1] = len(Name) + 2
        Handle = Middle.find(b"\x82\xc0\x01\x00", Marker)
        Middle[Handle + 4 : Handle + 6] = Encode(Value).to_bytes(2, "little")
        Delta = len(Name) - len(OldText)
        Bodies.append(
            BuildSection(
                Section(
                    SectionValue.version,
                    SectionValue.kind,
                    SectionValue.flags,
                    SectionValue.stamp,
                    SectionValue.part_name,
                    SectionValue.counts,
                    SectionValue.pointer + Delta,
                    SectionValue.ref_count,
                    list(SectionValue.refs),
                    list(SectionValue.classes),
                    bytes(Middle),
                    SectionValue.record_area,
                    SectionValue.digest,
                )
            )
        )
    Payload = SplicePayload(Payload, Bodies)
    return RebuildSplm(Parsed, {"/Root/UG_PART/UG_PART": Payload})


def Main(ArgValues: list[str]) -> int:
    if len(ArgValues) != 4:
        print("usage: ExprAuthor.py <template.prt> <name> <value> <target.prt>")
        return 2
    Data = Rewrite(
        FilePath(ArgValues[0]).read_bytes(), ArgValues[1].encode(), float(ArgValues[2])
    )
    FilePath(ArgValues[3]).write_bytes(Data)
    print("wrote", ArgValues[3], len(Data))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
