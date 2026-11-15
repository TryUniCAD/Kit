from __future__ import annotations
import sys
from pathlib import Path

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.Reader import OpenContainer


def Main(ArgValues: list[str]) -> int:
    DataValue = Path(ArgValues[0]).read_bytes()
    _, Streams, KindValue = OpenContainer(DataValue)
    print("container", KindValue, "streams", list(Streams))
    PartData = Streams.get("UG_PART/UG_PART") or Streams.get("UG_PART")
    if PartData is None:
        raise SystemExit("no UG_PART stream")
    Payload = ReadPayload(PartData)
    print("legacy", Payload.legacy, "sections", len(Payload.sections))
    for Index, Section in enumerate(Payload.sections):
        print(
            "section",
            Index,
            "start",
            hex(Section.offset),
            "body",
            hex(Section.body_offset),
            "size",
            Section.size,
            "end",
            hex(Section.body_offset + Section.size),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
