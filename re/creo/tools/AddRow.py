"""Research probe: turn the control's reserved row into a new named section.

The empty control already reserves space it calls `EMPTY_SPACE_FOR_REUSE` — two rows of padding, `1361` and
`157` bytes. That is a slot a new section can occupy without extending the directory tables: the row is
renamed, its body is replaced, and every later offset is recomputed by the subset builder.

It exists to answer whether a section the datum-only control does not have (here `FeatDefs`, which carries
Creo's dimensions) can be added at all, and what Creo says when it is.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "re/creo/tools")

import Subset
from convert.adapters.creo.Header import ReadHeader

KReserved = 157


def RenameRow(DataValue: bytes, Row: Subset.Row, NewName: str) -> bytes:
    Text = DataValue[Row.position : Row.position + Subset.KWidth]
    Fields = Text.decode("latin-1").rstrip("#\r\n").split()
    Fields[0] = NewName
    Line = " ".join(Fields).encode("ascii")
    Line = Line.ljust(Subset.KWidth - 1, b"#")[: Subset.KWidth - 1] + b"\n"
    Start = Row.position
    End = Row.position + Subset.KWidth
    return DataValue[:Start] + Line + DataValue[End:]


def Build(Source: Path, Payload: bytes, Target: Path, NameText: str = "FeatDefs") -> bytes:
    DataValue = Source.read_bytes()
    Header = ReadHeader(DataValue)
    Row = None
    for TableValue in Subset.ReadTables(DataValue, Header.base):
        for Entry in TableValue.rows:
            if Entry.name == "EMPTY_SPACE_FOR_REUSE" and Entry.length == KReserved:
                Row = Entry
    if Row is None:
        raise SystemExit("the reserved 157-byte row was not found")
    Renamed = RenameRow(DataValue, Row, NameText)
    Body = b"#" + NameText.encode("latin-1") + b"\n" + Payload
    Result = Subset.Build(Renamed, ReadHeader(Renamed).base, set(), {NameText: Body})
    Target.write_bytes(Result)
    print(f"{Target.name}: {len(Result)} bytes, {NameText} body {len(Body)} (reserved {KReserved})")
    return Result


def Compare(Source: Path, Target: Path) -> None:
    def Bodies(PathValue: Path) -> dict[str, bytes]:
        DataValue = PathValue.read_bytes()
        Header = ReadHeader(DataValue)
        Found: dict[str, bytes] = {}
        for TableValue in Subset.ReadTables(DataValue, Header.base):
            for Entry in TableValue.rows:
                if Entry.name.startswith("#") or Entry.name == "NEXT_TOC_ENTRY":
                    continue
                Absolute = Header.base + Entry.offset
                Found[Entry.name] = DataValue[Absolute : Absolute + Entry.length]
        return Found

    Before = Bodies(Source)
    After = Bodies(Target)
    Changed = sorted(n for n in Before if n in After and Before[n] != After[n])
    print(f"  rows before {len(Before)}, after {len(After)}")
    print(f"  new rows: {sorted(set(After) - set(Before))}")
    print(f"  changed existing rows: {Changed}")


if __name__ == "__main__":
    SourcePath = Path("re/creo/oracle/empty/solid_start_part_mmks.prt")
    sys.path.insert(0, "src")
    from convert.adapters.creo import Author

    Payload = Path(sys.argv[1]).read_bytes() if len(sys.argv) > 1 else Author.DefaultFeatDefs()
    TargetPath = Path.home() / "Documents/creo-authored" / (sys.argv[2] if len(sys.argv) > 2 else "featdefs.prt")
    Build(SourcePath, Payload, TargetPath)
    Compare(SourcePath, TargetPath)
