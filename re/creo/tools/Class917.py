"""Research probe: write a generated definition into the class-917 table.

The ladder's `FeatDefs` row holds two class tables: `feat_defs_949` (one element, a datum definition) and
`feat_defs_917` (one element of field index `0xC4`). Parsing the second shows it opens like the first —
`f7 03` <id> <symbol_key> <model_type> `e1` `e3` — and then its `place_rec_ptr` carries
`place_instruction_ptrs`, `plin_info_arr`, `outline` and `next_outline` records that reference geometry ids.

This probe replaces the class-917 element with one this module generates, keeping the rest of the ladder's row
untouched, so a refusal isolates the element itself. Vendor content is used here as a research oracle only.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "re/creo/tools")

import Subset
from convert.adapters.creo import Author
from convert.adapters.creo.Header import ReadHeader


def ProtrusionElement(
    FeatureId: int, DimensionValue: tuple[float, ...] = (100.0,)
) -> bytes:
    Element = b"\xE3"
    Element += b"\xF7\x03"
    Element += Author.SignedInt(FeatureId)
    Element += Author.SignedInt(-1)
    Element += Author.SignedInt(2)
    Element += b"\xE1"
    Element += Author.StructHeader("place_rec_ptr") + Author.PlacementRecord()
    Element += Author.FieldValue(
        0,
        "dimtab_ptr",
        b"\xF8" + Author.CompactInt(len(DimensionValue)) + b"\xF7\x03\xFB",
    )
    for Value in DimensionValue:
        Element += b"\xE2"
        Element += Author.FieldValue(1, "type", Author.SignedInt(1))
        Element += Author.FieldValue(2, "value", Author.ScalarValue(Value))
        Element += Author.FieldValue(1, "direct", Author.SignedInt(-1))
        Element += Author.FieldValue(2, "aux_value", Author.ScalarValue(Value))
        Element += Author.FieldValue(1, "ext_id", Author.SignedInt(-1))
        Element += Author.FieldValue(0, "dispdimattr", Author.SignedInt(0))
        Element += Author.FieldValue(1, "dimattr", Author.SignedIntArray((0,) * 7))
        Element += b"\xF2"
    return Element


def WholeRow(Source: Path, FeatureId: int, DatumId: int) -> bytes:
    DataValue = Source.read_bytes()
    Header = ReadHeader(DataValue)
    Payload = None
    for TableValue in Subset.ReadTables(DataValue, Header.base):
        for Entry in TableValue.rows:
            if Entry.name == "FeatDefs":
                Offset = Header.base + Entry.offset
                Body = DataValue[Offset : Offset + Entry.length]
                Payload = Body[Body.find(b"\n") + 1 :]
    if Payload is None:
        raise SystemExit("the ladder has no FeatDefs row")
    Payload = b"\xE0\x00Sld_FeatDefs\x00\xE3"
    Payload += b"\xE0\x00feat_defs_949\x00\xF8\x01\xF7\x02\xFB"
    Payload += b"\xE2" + Author.FeatDefBlock(DatumId, (100.0, 42.5))[1:]
    Payload += b"\xE0\x00feat_defs_917\x00\xF4\x06\xF8\x01\xF7\x80\xC4\xFB"
    Payload += ProtrusionElement(FeatureId)
    return Payload


def BuildWhole(Source: Path, FeatureId: int, DatumId: int, Target: Path) -> bytes:
    DataValue = Source.read_bytes()
    Header = ReadHeader(DataValue)
    NewPayload = WholeRow(Source, FeatureId, DatumId)
    Result = Subset.Build(
        DataValue, Header.base, set(), {"FeatDefs": b"#FeatDefs\n" + NewPayload}
    )
    Target.write_bytes(Result)
    print(f"{Target.name}: {len(Result)} bytes; whole row {len(NewPayload)} bytes")
    return Result


def Build(Source: Path, FeatureId: int, Target: Path) -> bytes:
    DataValue = Source.read_bytes()
    Header = ReadHeader(DataValue)
    Payload = None
    for TableValue in Subset.ReadTables(DataValue, Header.base):
        for Entry in TableValue.rows:
            if Entry.name == "FeatDefs":
                Offset = Header.base + Entry.offset
                Body = DataValue[Offset : Offset + Entry.length]
                Payload = Body[Body.find(b"\n") + 1 :]
    if Payload is None:
        raise SystemExit("the ladder has no FeatDefs row")
    DeclIndex = Payload.find(b"\xE0\x00feat_defs_917\x00")
    if DeclIndex < 0:
        raise SystemExit("the ladder has no class-917 table")
    Head = Payload[:DeclIndex]
    Table = b"\xE0\x00feat_defs_917\x00\xF4\x06\xF8\x01\xF7\x80\xC4\xFB"
    NewPayload = Head + Table + ProtrusionElement(FeatureId)
    Result = Subset.Build(
        DataValue, Header.base, set(), {"FeatDefs": b"#FeatDefs\n" + NewPayload}
    )
    Target.write_bytes(Result)
    print(
        f"{Target.name}: {len(Result)} bytes; element {len(ProtrusionElement(FeatureId))}, "
        f"payload {len(Payload)} -> {len(NewPayload)}"
    )
    return Result


if __name__ == "__main__":
    Home = Path.home() / "Documents/creo-authored"
    Build(
        Path("re/creo/oracle/ladder/ladder1.prt.2"),
        74,
        Home / "class917_element.prt",
    )
    BuildWhole(
        Path("re/creo/oracle/ladder/ladder1.prt.2"),
        74,
        66,
        Home / "class917_whole.prt",
    )
