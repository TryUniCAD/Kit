"""Research-only Creo PSB container rebuild with section drop and replace.

This tool reconstructs a PSB container from its own directory and rewrites every
row, every `NEXT_TOC_ENTRY` link, and every section offset after sections are
removed or replaced. It exists to answer one question the author cannot answer
on its own: which sections a part must carry before Creo accepts it as a model.
Vendor files used here are research oracles and are never shipped.

The layout rules this encodes were measured on the retained control:

- sections are physically ordered and each is followed by its own gap bytes,
  usually a literal `#\\n` line that is excluded from the stored length;
- the directory is a chain of tables linked by `NEXT_TOC_ENTRY`;
- column 7 is `-1` for kinds `9`, `11`, `b` and for free space, `2` for kind
  `12`, and `1` otherwise;
- a row whose name starts with `#` is padding and is skipped;
- the file ends with `#END_OF_UGC`.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as MakeField
from pathlib import Path
import sys

KWidth = 81
KVersion = "1934"


@dataclass
class Row:
    name: str
    offset: int
    length: int
    expanded: int
    kind: str
    count: str
    checksum_a: str
    checksum_b: str
    position: int


@dataclass
class Table:
    head: bytes
    count: int = 0
    rows: list[Row] = MakeField(default_factory=list)
    start: int = 0
    data_start: int = 0

    @property
    def size(self) -> int:
        return len(self.head) + KWidth * self.count


def ReadTable(DataValue: bytes, Position: int) -> Table:
    LineEnd = DataValue.find(b"\n", Position)
    Head = DataValue[Position : LineEnd + 1]
    Words = Head.decode("latin-1").rstrip("#\r\n").split()
    Count = int(Words[2])
    Width = int(Words[3])
    Cursor = LineEnd + 1
    Rows: list[Row] = []
    for _ in range(Count):
        Text = DataValue[Cursor : Cursor + Width]
        Fields = Text.decode("latin-1").rstrip("#\r\n").split()
        if Fields and len(Fields) >= 9:
            Rows.append(
                Row(
                    Fields[0],
                    int(Fields[1], 16),
                    int(Fields[2], 16),
                    int(Fields[3], 16),
                    Fields[5],
                    Fields[6],
                    Fields[7],
                    Fields[8],
                    Cursor,
                )
            )
        Cursor += Width
    return Table(Head, Count, Rows, Position, Cursor)


def RowValue(RowData: Row) -> bytes:
    Text = (
        f"{RowData.name} {RowData.offset:x} {RowData.length:x} "
        f"{RowData.expanded:x} {KVersion} {RowData.kind} {RowData.count} "
        f"{RowData.checksum_a} {RowData.checksum_b}"
    )
    return Text.encode("ascii").ljust(KWidth - 1, b"#")[: KWidth - 1] + b"\n"


def KindCount(RowData: Row) -> str:
    if RowData.kind in ("9", "11", "b") or RowData.name == "EMPTY_SPACE_FOR_REUSE":
        return "-1"
    if RowData.kind == "12":
        return "2"
    return "1"


def ReadTables(DataValue: bytes, Base: int) -> list[Table]:
    Tables: list[Table] = []
    Position = DataValue.find(b"#UGC_TOC", Base)
    while True:
        TableValue = ReadTable(DataValue, Position)
        Tables.append(TableValue)
        Link = next(
            (Entry for Entry in TableValue.rows if Entry.name == "NEXT_TOC_ENTRY"), None
        )
        if Link is None:
            break
        Position = Base + Link.offset
    return Tables


def Build(
    DataValue: bytes,
    Base: int,
    Drop: set[str],
    Replace: dict[str, bytes],
    KeepSpace: set[str] | None = None,
    Blank: set[str] | None = None,
) -> bytes:
    Reserve = KeepSpace or set()
    Blanked = Blank or set()
    Tables = ReadTables(DataValue, Base)
    Banner = DataValue[Base : Tables[0].start]
    Extents: dict[int, tuple[Row, bytes]] = {}
    for TableValue in Tables:
        for Entry in TableValue.rows:
            if Entry.name == "NEXT_TOC_ENTRY":
                continue
            Absolute = Base + Entry.offset
            Extents[Absolute] = (Entry, DataValue[Absolute : Absolute + Entry.length])
    Ordered = sorted(Extents)
    EndValue = Tables[-1].start
    def RegionEnd(Absolute: int) -> int:
        Holder = 0
        for IndexValue, TableValue in enumerate(Tables):
            if TableValue.data_start <= Absolute:
                Holder = IndexValue
        if Holder + 1 < len(Tables):
            return Tables[Holder + 1].start
        return EndValue

    Bodies: list[tuple[int, bytes, bytes, str]] = []
    for IndexValue, Absolute in enumerate(Ordered):
        Entry, Body = Extents[Absolute]
        if IndexValue + 1 < len(Ordered):
            FollowOn = Ordered[IndexValue + 1]
        else:
            FollowOn = EndValue
        FollowOn = min(FollowOn, RegionEnd(Absolute))
        Gap = DataValue[Absolute + Entry.length : FollowOn]
        if Entry.name in Drop:
            continue
        if Entry.name in Reserve:
            Bodies.append((Absolute, b"#" * Entry.length, Gap, Entry.name))
            continue
        NewBody = Replace.get(Entry.name, Body)
        if Entry.name in Blanked:
            NewBody = b"#" * Entry.length
        if Entry.name in Replace:
            Gap = b"#\n"
        Bodies.append((Absolute, NewBody, Gap, Entry.name))

    def RegionList(IndexValue: int) -> list[tuple[int, bytes, bytes]]:
        Bounds = Tables[IndexValue + 1].start if IndexValue + 1 < len(Tables) else None
        Low = Tables[IndexValue].data_start
        return [
            (Absolute, NewBody, Gap)
            for Absolute, NewBody, Gap, _Name in Bodies
            if Absolute >= Low and (Bounds is None or Absolute < Bounds)
        ]

    Chunks = [
        b"".join(NewBody + Gap for _, NewBody, Gap in RegionList(Index))
        for Index in range(len(Tables))
    ]
    TableOffset: list[int] = []
    Position = len(Banner)
    for IndexValue in range(len(Tables)):
        TableOffset.append(Position)
        Position += Tables[IndexValue].size + len(Chunks[IndexValue])
    NewOffset: dict[int, int] = {}
    for IndexValue in range(len(Tables)):
        Cursor = TableOffset[IndexValue] + Tables[IndexValue].size
        for Absolute, NewBody, Gap in RegionList(IndexValue):
            NewOffset[Absolute] = Cursor
            Cursor += len(NewBody) + len(Gap)
    Out = DataValue[:Base] + Banner
    for IndexValue, TableValue in enumerate(Tables):
        Lines = b""
        for Entry in TableValue.rows:
            if Entry.name == "NEXT_TOC_ENTRY":
                continue
            Absolute = Base + Entry.offset
            if Absolute not in NewOffset or Entry.name in Reserve:
                Lines += b"#" * (KWidth - 1) + b"\n"
                continue
            Entry.offset = NewOffset[Absolute]
            Entry.length = len(Replace.get(Entry.name, Extents[Absolute][1]))
            if Entry.name in Replace:
                Entry.expanded = Entry.length - len(Entry.name) - 2
                Entry.kind = "9"
                Entry.checksum_a = f"{sum(Replace[Entry.name]) & 0xFFFF:04x}"
            Entry.count = KindCount(Entry)
            Lines += RowValue(Entry)
        Link = next(
            (Entry for Entry in TableValue.rows if Entry.name == "NEXT_TOC_ENTRY"), None
        )
        if Link is not None:
            Link.offset = TableOffset[IndexValue + 1]
            Link.length = Tables[IndexValue + 1].size
            Link.expanded = 0
            Link.kind = "1"
            Link.count = "-1"
            Link.checksum_a = "0000"
            Link.checksum_b = "0000"
            Lines += RowValue(Link)
        Written = Lines.count(b"\n")
        if Written < TableValue.count:
            Lines += (b"#" * (KWidth - 1) + b"\n") * (TableValue.count - Written)
        Out += TableValue.head + Lines + Chunks[IndexValue]
    Out += DataValue[Tables[-1].data_start :]
    return Out


def SectionNames(DataValue: bytes, Base: int) -> list[str]:
    Names: list[str] = []
    for TableValue in ReadTables(DataValue, Base):
        for Entry in TableValue.rows:
            if Entry.name != "NEXT_TOC_ENTRY":
                Names.append(Entry.name)
    return Names


if __name__ == "__main__":
    sys.path.insert(0, "src")
    from convert.adapters.creo.Header import ReadHeader

    SourcePath = Path(sys.argv[1])
    TargetPath = Path(sys.argv[2])
    DropSet: set[str] = set()
    if len(sys.argv) > 3 and sys.argv[3]:
        DropSet = set(sys.argv[3].split(","))
    SourceData = SourcePath.read_bytes()
    HeaderValue = ReadHeader(SourceData)
    if DropSet == {"?"}:
        for NameValue in SectionNames(SourceData, HeaderValue.base):
            print(NameValue)
        raise SystemExit(0)
    Result = Build(SourceData, HeaderValue.base, DropSet, {})
    TargetPath.write_bytes(Result)
    print(f"{SourcePath} -> {TargetPath} {len(Result)} bytes, drop {sorted(DropSet)}")
