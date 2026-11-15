"""CATIA parametric vocabulary extractor.

The OSMX symbol table of a natively modelled CATPart names every class and
property the part uses. A dumb solid imported from another system carries only
product metadata (`ASMPRODUCT`, `PRDREP`, `MechanicalPart`, `_FtrList`,
`_ReferencePlanes`, `GSMPlane`, `xy-plane`). A parametric part additionally
carries the modelling vocabulary (`PRTSketch`, `Sketch`, `Pad`, `Pocket`,
`Shaft`, `Constraints`, `2DLine`, `2DCircle`, `ConstraintDYS`, ...).

This tool reads the largest OSMX stream of a CATPart, decodes its symbol table,
and reports the feature vocabulary. It is a research tool: it does not decode
the feature records themselves, only the class and property names that the
records reference.

Recovered from the CATIA V5-6R2022 install sample corpus. The symbol table
format is:

    OSMX <header> ... <u32 symbol_table_offset> <object graph> |\\x02 <u32 section_length> <symbol data>

Each symbol is a length byte followed by `length - 1` ASCII bytes. A length of
zero means the next four bytes are a little-endian u32 length and the value is
that many bytes. Values may contain newlines (design-table text).
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "src"))

from convert.adapters.catia.Container import CfvTwoArchive, OsmxArchive

KFeatureWords = (
    "sketch",
    "pad",
    "pocket",
    "shaft",
    "groove",
    "revolution",
    "chamfer",
    "fillet",
    "hole",
    "pattern",
    "mirror",
    "constraint",
    "dimension",
    "2dline",
    "2dcircle",
    "2dpoint",
    "2dspline",
)


def LargestOsmx(Archive: CfvTwoArchive) -> tuple[str, OsmxArchive] | None:
    Best: tuple[str, OsmxArchive] | None = None
    for Folder in [Archive.outer] + list(Archive.nested):
        for Stream in Folder.streams:
            try:
                Data = Archive.stream_bytes(Stream, Folder)
            except Exception:
                continue
            if not Data.startswith(b"OSMX"):
                continue
            try:
                Parsed = OsmxArchive.from_bytes(Data)
            except Exception:
                continue
            if Best is None or len(Parsed.symbols) > len(Best[1].symbols):
                Best = (Stream.name, Parsed)
    return Best


def FeatureWords(Symbols: tuple[str, ...]) -> list[str]:
    return sorted(
        {
            Value
            for Value in Symbols
            if Value and any(Word in Value.lower() for Word in KFeatureWords)
        }
    )


def Classify(PathValue: Path) -> tuple[str, int, list[str]]:
    Archive = CfvTwoArchive.from_bytes(PathValue.read_bytes())
    Found = LargestOsmx(Archive)
    if Found is None:
        return ("no-osmx", 0, [])
    _, Parsed = Found
    Values = tuple(Symbol.value for Symbol in Parsed.symbols)
    Words = FeatureWords(Values)
    Kind = "parametric" if Words else "dumb"
    return (Kind, len(Values), Words)


def Main() -> None:
    Base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("re/catia/examples")
    for PathValue in sorted(Base.rglob("*.CATPart")):
        if not PathValue.is_file():
            continue
        Kind, Count, Words = Classify(PathValue)
        print(f"{PathValue.name:56s} {Kind:10s} symbols={Count:4d} {Words[:8]}")


if __name__ == "__main__":
    Main()
