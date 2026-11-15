"""Research probe: a class-949 definition that carries a generated sketch.

The ladder's `949` element is mapped through 191 declared headers. This probe emits the part of it that carries
a definition: `id`, `symbol_key`, `model_type`, `group_info_ptr`, `place_rec_ptr`, then `sub_feat_arr` with one
section element (`type 160`, `data(subft_indexnumber)`, `expl_state_ref`, `feat_outl_info`, the roll-back fields,
`parchild_table`, `copy_info_ptr`, `embed_info_ptr`) and `gsec_ptr` whose `gsec2d_ptr`/`segtab_ptr` holds four
line segments over four point ids, with a `dimtab_ptr` of four dimensions, a `relat_ptr` and a `formula_ptr`.

Coordinates are not emitted because the format does not store them: the solver derives the points from the
segments, the relations and the dimensions at regeneration.

The element is paired with the already-accepted generated class-917 element and substituted into the ladder's
`FeatDefs` row. Vendor content is used here as a research oracle only.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "re/creo/tools")

import Subset
from convert.adapters.creo import Author
from convert.adapters.creo.Header import ReadHeader

KPoints = ((0, 1), (1, 2), (2, 3), (3, 0))
KDimensions = (10.0, 20.0, 10.0, 20.0)
KOutline = (184.50782059963194, 0.0, 115.65227549271083, -154.4303300690026, 0.0, -86.06680966899467)


def Segment(FirstPoint: int, SecondPoint: int, ExtId: int, Declare: bool) -> bytes:
    Payload = b"\xE2"
    Payload += Author.FieldValue(1, "type", Author.SignedInt(2))
    Payload += Author.FieldValue(
        1,
        "dir",
        b"\xF8\x03" + Author.SignedInt(-1) + Author.SignedInt(0) + Author.SignedInt(0),
    )
    Payload += Author.FieldValue(
        1,
        "pointid",
        b"\xF8\x02" + Author.SignedInt(FirstPoint) + Author.SignedInt(SecondPoint),
    )
    Payload += Author.FieldValue(1, "cntrid", Author.SignedInt(-1))
    Payload += Author.FieldValue(1, "arcorient", Author.SignedInt(0))
    Payload += Author.FieldValue(1, "verhor", Author.SignedInt(1))
    Payload += Author.FieldValue(1, "radius", Author.SignedInt(-1))
    Payload += Author.FieldValue(1, "radius2", Author.SignedInt(-1))
    Payload += Author.FieldValue(1, "ext_id", Author.SignedInt(ExtId))
    Payload += Author.StructHeader("gen_info") + b"\xE2"
    Payload += Author.StructHeader("known_ent_info") + b"\xF1\xE2"
    Payload += Author.FieldValue(1, "attr", Author.SignedInt(0))
    Payload += Author.FieldValue(1, "known_ent_id", Author.SignedInt(-1))
    Payload += b"\xF2"
    if not Declare:
        Payload = Payload.replace(b"\xE0", b"\xE0", 1)
    return Payload


def Dimension(Value: float, ExtId: int) -> bytes:
    Payload = b"\xE2"
    Payload += Author.FieldValue(1, "type", Author.SignedInt(1))
    Payload += Author.FieldValue(2, "value", Author.ScalarValue(Value))
    Payload += Author.FieldValue(1, "direct", Author.SignedInt(0))
    Payload += Author.FieldValue(2, "aux_value", Author.ScalarValue(1.0))
    Payload += Author.FieldValue(1, "ext_id", Author.SignedInt(ExtId))
    Payload += Author.FieldValue(0, "dispdimattr", Author.SignedInt(0))
    Payload += Author.FieldValue(1, "dimattr", Author.SignedIntArray((0,) * 7))
    Payload += b"\xF2"
    return Payload


def Sketch() -> bytes:
    Payload = Author.StructHeader("gsec_ptr") + b"\xF8\x01\xF7\x2A\xFB"
    Payload += b"\xE2"
    Payload += Author.FieldValue(1, "type", Author.SignedInt(2))
    Payload += Author.FieldValue(1, "is_ref_gsec", Author.SignedInt(0))
    Payload += Author.FieldValue(10, "name", b"Sketch 1\x00")
    Payload += Author.StructHeader("gsec2d_ptr") + b"\xE3"
    Payload += Author.StructHeader("segtab_ptr") + b"\xF8\x04\xF7\x2F\xFB"
    for IndexValue, (First, Second) in enumerate(KPoints):
        Payload += Segment(First, Second, 4 + IndexValue, IndexValue == 0)
    Payload += Author.StructHeader("attributes") + b"\xF0\x08\xF1\xF7\x3A"
    Payload += Author.StructHeader("dimtab_ptr") + b"\xF8\x04\xF7\x3E\xFB"
    for IndexValue, Value in enumerate(KDimensions):
        Payload += Dimension(Value, IndexValue)
    Payload += b"\xE0\x01formula_ptr\x00\xF8\x08"
    Payload += b"".join(Author.SignedInt(IndexValue) for IndexValue in range(8))
    Payload += b"\xE0\x01qind\x00" + Author.SignedInt(-1)
    Payload += Author.FieldValue(
        2, "fixed_origin", b"\xF8\x03" + Author.ScalarValue(0.0) + Author.ScalarValue(0.0)
    )
    Payload += Author.StructHeader("anchor") + b"\xE1"
    Payload += Author.FieldValue(1, "totalpointid", Author.SignedInt(len(KPoints)))
    Payload += Author.FieldValue(1, "checkarcs_flag", Author.SignedInt(1))
    Payload += Author.StructHeader("location") + b"\xE3"
    Payload += Author.FieldValue(1, "id", Author.SignedInt(-1))
    Payload += Author.FieldValue(2, "param", Author.ScalarValue(0.0))
    Payload += Author.FieldValue(1, "type", Author.SignedInt(-1))
    return Payload


def DimensionRef(FirstPoint: int, SecondPoint: int) -> bytes:
    Payload = Author.StructHeader("dim_ref") + b"\xF1\xF8\x02\xF7\x46\xFB"
    for ItemId, Sense in ((1, 4), (-1, -1)):
        Payload += b"\xE2"
        Payload += Author.FieldValue(1, "item_id", Author.SignedInt(ItemId))
        Payload += Author.FieldValue(1, "sense", Author.SignedInt(Sense))
        Payload += Author.FieldValue(
            1,
            "point",
            b"\xF8\x02"
            + Author.SignedInt(FirstPoint)
            + Author.SignedInt(SecondPoint),
        )
    return Payload


def Relation(IndexValue: int, FirstPoint: int, SecondPoint: int) -> bytes:
    Payload = b"\xE2"
    Payload += Author.FieldValue(1, "id", Author.SignedInt(IndexValue))
    Payload += Author.FieldValue(1, "used", Author.SignedInt(0))
    for NameText, Values in (
        ("a", (FirstPoint, SecondPoint, -1, -1)),
        ("b", (-1, -1, -1, -1)),
    ):
        Payload += Author.FieldValue(
            1,
            NameText,
            b"\xF8\x04"
            + b"".join(Author.SignedInt(Value) for Value in Values),
        )
    Payload += Author.FieldValue(
        2,
        "c",
        b"\xF8\x03"
        + Author.ScalarValue(0.0)
        + Author.ScalarValue(0.0)
        + Author.ScalarValue(0.0),
    )
    Payload += Author.FieldValue(1, "sign", Author.SignedInt(1))
    Payload += Author.FieldValue(1, "idim", Author.SignedInt(0))
    Payload += Author.FieldValue(1, "type", Author.SignedInt(0))
    return Payload


# the entity graph is one bucket per point with a single entry naming it
def EntityState(Count: int) -> bytes:
    Payload = Author.StructHeader("chains") + b"\xF8" + Author.CompactInt(Count)
    Payload += b"\xF7\x66\xFB"
    for IndexValue in range(Count):
        Payload += b"\xE2"
        if IndexValue == 0:
            Payload += Author.FieldValue(1, "bucket_index", Author.SignedInt(0))
            Payload += Author.StructHeader("bucket_xar") + b"\xF8\x00\xF7\x68\xFB"
        else:
            Payload += Author.SignedInt(IndexValue)
            Payload += b"\xF8\x00\xF7\x68\xFB"
        Payload += Author.StructHeader("ent_mode") + Author.SignedInt(0)
        Payload += Author.StructHeader("entry_ptr(entity_entry)") + b"\xE3"
        if IndexValue == 0:
            Payload += Author.FieldValue(1, "xid", Author.SignedInt(IndexValue))
        else:
            Payload += Author.SignedInt(IndexValue)
        if IndexValue == 0:
            Payload += Author.FieldValue(1, "ent_mode", Author.SignedInt(0))
            Payload += Author.FieldValue(1, "start_vtx", Author.SignedInt(-1))
            Payload += Author.FieldValue(1, "end_vtx", Author.SignedInt(-1))
            Payload += Author.FieldValue(1, "center_vtx", Author.SignedInt(-1))
            Payload += Author.FieldValue(1, "pers_attribs", Author.SignedInt(0))
        else:
            Payload += Author.SignedInt(0)
            Payload += Author.SignedInt(-1)
            Payload += Author.SignedInt(-1)
            Payload += Author.SignedInt(-1)
            Payload += Author.SignedInt(0)
        Payload += b"\xF2"
    return Payload


def SolverTables(PointCount: int, EntityCount: int = 0) -> bytes:
    Payload = Author.StructHeader("relat_ptr") + b"\xF4\x04\xF8\x08\xF7\x4A\xFB"
    for IndexValue in range(PointCount):
        Payload += Relation(IndexValue, IndexValue, (IndexValue + 1) % PointCount)
    Payload += b"\xE0\x01formula_ptr\x00\xF8\x08"
    Payload += b"".join(Author.SignedInt(IndexValue) for IndexValue in range(8))
    Payload += b"\xE0\x01qind\x00" + Author.SignedInt(-1)
    Payload += Author.FieldValue(
        2,
        "fixed_origin",
        b"\xF8\x03" + Author.ScalarValue(0.0) + Author.ScalarValue(0.0),
    )
    Payload += Author.StructHeader("anchor") + b"\xE1"
    Payload += Author.FieldValue(1, "totalpointid", Author.SignedInt(PointCount))
    Payload += Author.FieldValue(1, "checkarcs_flag", Author.SignedInt(1))
    Payload += Author.StructHeader("location") + b"\xE3"
    Payload += Author.FieldValue(1, "id", Author.SignedInt(-1))
    Payload += Author.FieldValue(2, "param", Author.ScalarValue(0.0))
    Payload += Author.FieldValue(1, "type", Author.SignedInt(-1))
    Payload += Author.StructHeader("nsket_info") + b"\xF1\xE3"
    Payload += Author.FieldValue(2, "scale", Author.ScalarValue(1.0))
    Payload += Author.FieldValue(1, "last_was_permanent", Author.SignedInt(0))
    Payload += Author.StructHeader("unsolved_ptr") + b"\xF1\xE3"
    Payload += Author.FieldValue(10, "iges_file", b"\xE1")
    Payload += Author.FieldValue(1, "solve_version", b"\xF1\x01")
    Payload += Author.StructHeader("ent_tab") + b"\xE3"
    Payload += Author.FieldValue(1, "next_available_xid", Author.SignedInt(PointCount))
    Payload += Author.FieldValue(1, "bucket_index", Author.SignedInt(0))
    # the entity table is emitted structurally with empty arrays rather than as a null
    Payload += Author.StructHeader("bucket_xar") + b"\xF8\x00"
    Payload += Author.StructHeader("vert_tab") + b"\xF1\xE3"
    Payload += Author.FieldValue(1, "next_available_xid", Author.SignedInt(PointCount))
    Payload += EntityState(EntityCount) if EntityCount else b""
    Payload += Author.StructHeader("skamp_ptr") + b"\xF3\xF8\x08\xF7\x7A\xFB"
    for IndexValue in range(PointCount):
        Payload += b"\xE2"
        Payload += Author.FieldValue(1, "id", Author.SignedInt(IndexValue))
        Payload += Author.FieldValue(1, "type", Author.SignedInt(0))
        Payload += Author.FieldValue(1, "flags", Author.SignedInt(0))
        Payload += Author.FieldValue(1, "status", Author.SignedInt(0))
        Payload += Author.StructHeader("items") + b"\xE1"
    Payload += Author.StructHeader("triples_ptr") + b"\xF4\x04\xF8\x08\xF7\x80\x82\xFB"
    for IndexValue in range(PointCount):
        Payload += b"\xE2"
        Payload += Author.FieldValue(1, "rel_id", Author.SignedInt(IndexValue))
        Payload += Author.FieldValue(1, "eqn_id", Author.SignedInt(-1))
        Payload += Author.FieldValue(1, "skamp_id", Author.SignedInt(IndexValue))
    Payload += Author.StructHeader("rigid_chains_ptr") + b"\xF2\xE1"
    Payload += Author.StructHeader("p_raw_pool") + b"\xE1"
    Payload += Author.StructHeader("sket_pattern_info") + b"\xE3"
    Payload += Author.StructHeader("gsec3d_ptr") + b"\xF2\xE3"
    Payload += Author.FieldValue(1, "type", Author.SignedInt(7))
    Payload += Author.FieldValue(1, "flip", Author.SignedInt(1))
    Payload += Author.FieldValue(1, "own_ref_id", Author.SignedInt(-1))
    Payload += Author.StructHeader("first_chain_ptr") + b"\xE3"
    Payload += Author.FieldValue(1, "quilt_id", Author.SignedInt(-1))
    Payload += Author.FieldValue(1, "plane_id", Author.SignedInt(0))
    Payload += Author.FieldValue(1, "plane_flip", Author.SignedInt(0))
    Payload += Author.StructHeader("ref_planes") + b"\xF8\x00"
    Payload += Author.StructHeader("save_entity_ptr(line)") + b"\xE3"
    Payload += Author.FieldValue(1, "id", Author.SignedInt(-1))
    Payload += Author.FieldValue(1, "type", Author.SignedInt(0))
    Payload += Author.StructHeader("back_entity_ptr(line)") + b"\xE1"
    Payload += Author.StructHeader("order_table") + b"\xF8\x00"
    Payload += Author.StructHeader("order_tab") + b"\xF1\xE3"
    Payload += Author.StructHeader("p_saved_result") + b"\xE3"
    Payload += Author.StructHeader("draft_setup_ptr") + b"\xE3"
    Payload += Author.FieldValue(1, "grid_displayed", Author.SignedInt(0))
    Payload += Author.FieldValue(1, "grid_origin_displayed", Author.SignedInt(0))
    Payload += Author.StructHeader("grid") + b"\xE2"
    Payload += Author.FieldValue(1, "grid_type", Author.SignedInt(0))
    Payload += Author.FieldValue(
        2,
        "origin",
        b"\xF8\x03" + Author.ScalarValue(0.0) + Author.ScalarValue(0.0),
    )
    Payload += Author.StructHeader("grid_params(cart_params)") + b"\xE2"
    Payload += Author.FieldValue(2, "x_spacing", Author.ScalarValue(1.0))
    Payload += Author.FieldValue(2, "y_spacing", Author.ScalarValue(1.0))
    Payload += Author.FieldValue(2, "angle", Author.ScalarValue(0.0))
    return Payload


def FullDefinitionBlock(FeatureId: int) -> bytes:
    Payload = b"\xE3"
    Payload += Author.FieldValue(1, "id", Author.SignedInt(FeatureId))
    Payload += Author.FieldValue(1, "symbol_key", Author.SignedInt(-1))
    Payload += Author.FieldValue(1, "model_type", Author.SignedInt(2))
    Payload += Author.StructHeader("group_info_ptr") + b"\xE1"
    Payload += Author.StructHeader("place_rec_ptr") + Author.PlacementRecord()
    Payload += Author.StructHeader("sub_feat_arr") + b"\xF8\x01\xF7\x17\xFB"
    Payload += b"\xE3"
    Payload += Author.FieldValue(1, "id", Author.SignedInt(0))
    Payload += Author.FieldValue(1, "type", Author.SignedInt(160))
    Payload += Author.FieldValue(1, "sub_type", Author.SignedInt(-1))
    Payload += Author.StructHeader("data(subft_indexnumber)") + b"\xE3"
    Payload += Author.FieldValue(1, "index", Author.SignedInt(1))
    Payload += Author.FieldValue(1, "tool_type", Author.SignedInt(60001))
    Payload += Author.FieldValue(1, "sep_index", Author.SignedInt(-1))
    Payload += Author.StructHeader("expl_state_ref") + b"\xF3\xE1"
    Payload += Author.StructHeader("feat_outl_info") + b"\xE3"
    Payload += b"\xE0\x02ent_outl\x00\xF9\x02\x03" + Author.RunValues(KOutline)
    Payload += Author.FieldValue(1, "max_text_len", Author.SignedInt(0))
    Payload += Author.StructHeader("pre_roll_back") + b"\xE1"
    Payload += Author.StructHeader("post_roll_back") + b"\xE1"
    Payload += Author.StructHeader("post_regen") + b"\xE1"
    Payload += (
        Author.StructHeader("parchild_table")
        + b"\xF1\xE3"
        + b"\xE0\x09Structure_Invalid\x00"
        + Author.SignedInt(43981)
    )
    Payload += Author.StructHeader("copy_info_ptr") + b"\xF1\xE1"
    Payload += Author.StructHeader("embed_info_ptr") + b"\xE1"
    Payload += Sketch()
    Payload += Author.FieldValue(
        0,
        "dimtab_ptr",
        b"\xF8" + Author.CompactInt(len(KDimensions)) + b"\xF7\x3E\xFB",
    )
    for IndexValue, Value in enumerate(KDimensions):
        Payload += Dimension(Value, IndexValue)
    return Payload


def Build(Source: Path, Target: Path) -> bytes:
    DataValue = Source.read_bytes()
    Header = ReadHeader(DataValue)
    Row = (
        Author.StructHeader("Sld_FeatDefs")
        + b"\xE3"
        + Author.StructHeader("feat_defs_949")
        + b"\xF8\x01\xF7\x02\xFB"
        + DefinitionBlock(66)
        + Author.StructHeader("feat_defs_917")
        + b"\xF4\x06\xF8\x01\xF7\x80\xC4\xFB"
        + Author.SolidFeatureDefinition(74, (100.0,))
    )
    Result = Subset.Build(DataValue, Header.base, set(), {"FeatDefs": b"#FeatDefs\n" + Row})
    Target.write_bytes(Result)
    print(f"{Target.name}: {len(Result)} bytes; row {len(Row)}")
    return Result


if __name__ == "__main__":
    Home = Path.home() / "Documents/creo-authored"
    Build(Path("re/creo/oracle/ladder/ladder1.prt.2"), Home / "sketch949.prt")


def FullSketch() -> bytes:
    Payload = Author.StructHeader("gsec_ptr") + b"\xF8\x01\xF7\x2A\xFB"
    Payload += b"\xE2"
    Payload += Author.FieldValue(1, "type", Author.SignedInt(2))
    Payload += Author.FieldValue(1, "is_ref_gsec", Author.SignedInt(0))
    Payload += Author.FieldValue(10, "name", b"Sketch 1\x00")
    Payload += Author.StructHeader("gsec2d_ptr") + b"\xE3"
    Payload += Author.StructHeader("segtab_ptr") + b"\xF8\x04\xF7\x2F\xFB"
    for IndexValue, (First, Second) in enumerate(KPoints):
        Payload += Segment(First, Second, 4 + IndexValue, IndexValue == 0)
    Payload += b"\xE0\x01attributes\x00\xF0\x08\xF1\xF7\x3A"
    Payload += Author.StructHeader("dimtab_ptr") + b"\xF3\xF8\x04\xF7\x3E\xFB"
    for IndexValue, Value in enumerate(KDimensions):
        Payload += Dimension(Value, IndexValue)
        Payload += DimensionRef(IndexValue, (IndexValue + 1) % len(KPoints))
    Payload += SolverTables(len(KPoints))
    return Payload


def FullElement(FeatureId: int) -> bytes:
    Payload = b"\xE3"
    Payload += Author.FieldValue(1, "id", Author.SignedInt(FeatureId))
    Payload += Author.FieldValue(1, "symbol_key", Author.SignedInt(-1))
    Payload += Author.FieldValue(1, "model_type", Author.SignedInt(2))
    Payload += Author.StructHeader("group_info_ptr") + b"\xE1"
    Payload += Author.StructHeader("place_rec_ptr") + Author.PlacementRecord()
    Payload += Author.StructHeader("sub_feat_arr") + b"\xF8\x01\xF7\x17\xFB"
    Payload += b"\xE3"
    Payload += Author.FieldValue(1, "id", Author.SignedInt(0))
    Payload += Author.FieldValue(1, "type", Author.SignedInt(160))
    Payload += Author.FieldValue(1, "sub_type", Author.SignedInt(-1))
    Payload += Author.StructHeader("data(subft_indexnumber)") + b"\xE3"
    Payload += Author.FieldValue(1, "index", Author.SignedInt(1))
    Payload += Author.FieldValue(1, "tool_type", Author.SignedInt(60001))
    Payload += Author.FieldValue(1, "sep_index", Author.SignedInt(-1))
    Payload += Author.StructHeader("expl_state_ref") + b"\xF3\xE1"
    Payload += Author.StructHeader("feat_outl_info") + b"\xE3"
    Payload += b"\xE0\x02ent_outl\x00\xF9\x02\x03" + Author.RunValues(KOutline)
    Payload += Author.FieldValue(1, "max_text_len", Author.SignedInt(0))
    Payload += Author.StructHeader("pre_roll_back") + b"\xE1"
    Payload += Author.StructHeader("post_roll_back") + b"\xE1"
    Payload += Author.StructHeader("post_regen") + b"\xE1"
    Payload += (
        Author.StructHeader("parchild_table")
        + b"\xF1\xE3"
        + b"\xE0\x09Structure_Invalid\x00"
        + Author.SignedInt(43981)
    )
    Payload += Author.StructHeader("copy_info_ptr") + b"\xF1\xE1"
    Payload += Author.StructHeader("embed_info_ptr") + b"\xE1"
    Payload += FullSketch()
    Payload += Author.FieldValue(
        0,
        "dimtab_ptr",
        b"\xF8" + Author.CompactInt(len(KDimensions)) + b"\xF7\x3E\xFB",
    )
    for IndexValue, Value in enumerate(KDimensions):
        Payload += Dimension(Value, IndexValue)
        Payload += DimensionRef(IndexValue, (IndexValue + 1) % len(KPoints))
    return Payload


def BuildFull(Source: Path, Target: Path) -> bytes:
    DataValue = Source.read_bytes()
    Header = ReadHeader(DataValue)
    Row = (
        Author.StructHeader("Sld_FeatDefs")
        + b"\xE3"
        + Author.StructHeader("feat_defs_949")
        + b"\xF8\x01\xF7\x02\xFB"
        + FullElement(66)
        + Author.StructHeader("feat_defs_917")
        + b"\xF4\x06\xF8\x01\xF7\x80\xC4\xFB"
        + Author.SolidFeatureDefinition(74, (100.0,))
    )
    Result = Subset.Build(DataValue, Header.base, set(), {"FeatDefs": b"#FeatDefs\n" + Row})
    Target.write_bytes(Result)
    print(f"{Target.name}: {len(Result)} bytes; row {len(Row)}")
    return Result


def BuildHybrid(Source: Path, Target: Path) -> bytes:
    """Our generated prefix with the vendor's solver tail, to separate prefix from tail."""
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
    End = Payload.find(b"\xE0\x00feat_defs_917\x00")
    Vendor = Payload[37:End]
    Marker = b"\xE0\x00relat_ptr\x00"
    Ours = FullElement(66)
    Hybrid = Ours[: Ours.find(Marker)] + Vendor[Vendor.find(Marker) :]
    Row = (
        Author.StructHeader("Sld_FeatDefs")
        + b"\xE3"
        + Author.StructHeader("feat_defs_949")
        + b"\xF8\x01\xF7\x02\xFB"
        + Hybrid
        + Author.StructHeader("feat_defs_917")
        + b"\xF4\x06\xF8\x01\xF7\x80\xC4\xFB"
        + Author.SolidFeatureDefinition(74, (100.0,))
    )
    Result = Subset.Build(DataValue, Header.base, set(), {"FeatDefs": b"#FeatDefs\n" + Row})
    Target.write_bytes(Result)
    print(f"{Target.name}: {len(Result)} bytes; hybrid element {len(Hybrid)}")
    return Result


def BuildMirror(Source: Path, Target: Path) -> bytes:
    """The complement of BuildHybrid: the vendor's prefix with our generated solver tail."""
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
    End = Payload.find(b"\xE0\x00feat_defs_917\x00")
    Vendor = Payload[37:End]
    Marker = b"\xE0\x00relat_ptr\x00"
    Ours = FullElement(66)
    Mirror = Vendor[: Vendor.find(Marker)] + Ours[Ours.find(Marker) :]
    Row = (
        Author.StructHeader("Sld_FeatDefs")
        + b"\xE3"
        + Author.StructHeader("feat_defs_949")
        + b"\xF8\x01\xF7\x02\xFB"
        + Mirror
        + Author.StructHeader("feat_defs_917")
        + b"\xF4\x06\xF8\x01\xF7\x80\xC4\xFB"
        + Author.SolidFeatureDefinition(74, (100.0,))
    )
    Result = Subset.Build(DataValue, Header.base, set(), {"FeatDefs": b"#FeatDefs\n" + Row})
    Target.write_bytes(Result)
    print(f"{Target.name}: {len(Result)} bytes; mirror element {len(Mirror)}")
    return Result


KAlignedPoints = 8
KAlignedSegments = ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6))


def AlignedSketch() -> bytes:
    """The sketch with the vendor's counts: eight points, six segments, matching solver tables."""
    Payload = Author.StructHeader("gsec_ptr") + b"\xF8\x01\xF7\x2A\xFB"
    Payload += b"\xE2"
    Payload += Author.FieldValue(1, "type", Author.SignedInt(2))
    Payload += Author.FieldValue(1, "is_ref_gsec", Author.SignedInt(0))
    Payload += Author.FieldValue(10, "name", b"Sketch 1\x00")
    Payload += Author.StructHeader("gsec2d_ptr") + b"\xE3"
    Payload += Author.StructHeader("segtab_ptr") + b"\xF8\x06\xF7\x2F\xFB"
    for IndexValue, (First, Second) in enumerate(KAlignedSegments):
        Payload += Segment(First, Second, 4 + IndexValue, IndexValue == 0)
    Payload += b"\xE0\x01attributes\x00\xF0\x08\xF1\xF7\x3A"
    Payload += Author.StructHeader("dimtab_ptr") + b"\xF3\xF8\x04\xF7\x3E\xFB"
    for IndexValue, Value in enumerate(KDimensions):
        Payload += Dimension(Value, IndexValue)
        Payload += DimensionRef(IndexValue, (IndexValue + 1) % KAlignedPoints)
    Payload += SolverTables(KAlignedPoints)
    return Payload


def BuildAligned(Source: Path, Target: Path) -> bytes:
    DataValue = Source.read_bytes()
    Header = ReadHeader(DataValue)
    Element = b"\xE3"
    Element += Author.FieldValue(1, "id", Author.SignedInt(66))
    Element += Author.FieldValue(1, "symbol_key", Author.SignedInt(-1))
    Element += Author.FieldValue(1, "model_type", Author.SignedInt(2))
    Element += Author.StructHeader("group_info_ptr") + b"\xE1"
    Element += Author.StructHeader("place_rec_ptr") + Author.PlacementRecord()
    Element += Author.StructHeader("sub_feat_arr") + b"\xF8\x01\xF7\x17\xFB"
    Element += b"\xE3"
    Element += Author.FieldValue(1, "id", Author.SignedInt(0))
    Element += Author.FieldValue(1, "type", Author.SignedInt(160))
    Element += Author.FieldValue(1, "sub_type", Author.SignedInt(-1))
    Element += Author.StructHeader("data(subft_indexnumber)") + b"\xE3"
    Element += Author.FieldValue(1, "index", Author.SignedInt(1))
    Element += Author.FieldValue(1, "tool_type", Author.SignedInt(60001))
    Element += Author.FieldValue(1, "sep_index", Author.SignedInt(-1))
    Element += Author.StructHeader("expl_state_ref") + b"\xF3\xE1"
    Element += Author.StructHeader("feat_outl_info") + b"\xE3"
    Element += b"\xE0\x02ent_outl\x00\xF9\x02\x03" + Author.RunValues(KOutline)
    Element += Author.FieldValue(1, "max_text_len", Author.SignedInt(0))
    Element += Author.StructHeader("pre_roll_back") + b"\xE1"
    Element += Author.StructHeader("post_roll_back") + b"\xE1"
    Element += Author.StructHeader("post_regen") + b"\xE1"
    Element += Author.StructHeader("parchild_table") + b"\xF1\xE3"
    Element += b"\xE0\x09Structure_Invalid\x00" + Author.SignedInt(43981)
    Element += Author.StructHeader("copy_info_ptr") + b"\xF1\xE1"
    Element += Author.StructHeader("embed_info_ptr") + b"\xE1"
    Element += AlignedSketch()
    Row = (
        Author.StructHeader("Sld_FeatDefs")
        + b"\xE3"
        + Author.StructHeader("feat_defs_949")
        + b"\xF8\x01\xF7\x02\xFB"
        + Element
        + Author.StructHeader("feat_defs_917")
        + b"\xF4\x06\xF8\x01\xF7\x80\xC4\xFB"
        + Author.SolidFeatureDefinition(74, (100.0,))
    )
    Result = Subset.Build(DataValue, Header.base, set(), {"FeatDefs": b"#FeatDefs\n" + Row})
    Target.write_bytes(Result)
    print(f"{Target.name}: {len(Result)} bytes; aligned element {len(Element)}")
    return Result


def SubFeatBlock(FeatureId: int) -> bytes:
    """Our sub_feat_arr record alone, from its declaration up to gsec_ptr."""
    Element = FullElement(FeatureId)
    Start = Element.find(b"\xE0\x00sub_feat_arr\x00")
    End = Element.find(b"\xE0\x00gsec_ptr\x00")
    if Start < 0 or End < 0:
        raise SystemExit("our element has no sub_feat_arr or gsec_ptr")
    return Element[Start:End]


def BuildSubFeatSwap(Source: Path, Target: Path) -> bytes:
    """The vendor element with only our sub_feat_arr record, to test that record in isolation."""
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
    End = Payload.find(b"\xE0\x00feat_defs_917\x00")
    Vendor = Payload[37:End]
    Start = Vendor.find(b"\xE0\x00sub_feat_arr\x00")
    Tail = Vendor.find(b"\xE0\x00gsec_ptr\x00")
    Swapped = Vendor[:Start] + SubFeatBlock(66) + Vendor[Tail:]
    Row = (
        Author.StructHeader("Sld_FeatDefs")
        + b"\xE3"
        + Author.StructHeader("feat_defs_949")
        + b"\xF8\x01\xF7\x02\xFB"
        + Swapped
        + Author.StructHeader("feat_defs_917")
        + b"\xF4\x06\xF8\x01\xF7\x80\xC4\xFB"
        + Author.SolidFeatureDefinition(74, (100.0,))
    )
    Result = Subset.Build(DataValue, Header.base, set(), {"FeatDefs": b"#FeatDefs\n" + Row})
    Target.write_bytes(Result)
    print(f"{Target.name}: {len(Result)} bytes; sub-feature block {len(SubFeatBlock(66))}")
    return Result


# the measured topology of the ladder sketch: a closed rectangle plus two construction lines
KMeasuredSegments = (
    (2, (-1, 0, 0), (0, 1), 4, 1),
    (2, (0, 1, 0), (1, 2), 5, 0),
    (2, (1, 0, 0), (2, 3), 6, 1),
    (2, (0, -1, 0), (3, 0), 7, 0),
    (32770, (-1, 0, 0), (4, 5), 0, 1),
    (32770, (0, -1, 0), (6, 7), 1, 0),
)


def MeasuredSegment(TypeValue: int, Dir: tuple[int, int, int], Points, ExtId: int, VerHor: int, Declare: bool) -> bytes:
    Payload = b"\xE2"
    if Declare:
        Payload += Author.FieldValue(1, "type", Author.SignedInt(TypeValue))
        Payload += Author.FieldValue(
            1,
            "dir",
            b"\xF8\x03" + b"".join(Author.SignedInt(Value) for Value in Dir),
        )
        Payload += Author.FieldValue(
            1,
            "pointid",
            b"\xF8\x02" + Author.SignedInt(Points[0]) + Author.SignedInt(Points[1]),
        )
        Payload += Author.FieldValue(1, "cntrid", Author.SignedInt(-1))
        Payload += Author.FieldValue(1, "arcorient", Author.SignedInt(0))
        Payload += Author.FieldValue(1, "verhor", Author.SignedInt(VerHor))
        Payload += Author.FieldValue(1, "radius", Author.SignedInt(-1))
        Payload += Author.FieldValue(1, "radius2", Author.SignedInt(-1))
        Payload += Author.FieldValue(1, "ext_id", Author.SignedInt(ExtId))
        Payload += Author.StructHeader("gen_info") + b"\xE2"
        Payload += Author.StructHeader("known_ent_info") + b"\xF1\xE2"
        Payload += Author.FieldValue(1, "attr", Author.SignedInt(0))
        Payload += Author.FieldValue(1, "known_ent_id", Author.SignedInt(-1))
        Payload += b"\xF2"
        return Payload
    Payload += Author.SignedInt(TypeValue)
    Payload += b"".join(Author.SignedInt(Value) for Value in Dir)
    Payload += Author.SignedInt(Points[0]) + Author.SignedInt(Points[1])
    Payload += Author.SignedInt(-1)
    Payload += Author.SignedInt(0)
    Payload += Author.SignedInt(VerHor)
    Payload += Author.SignedInt(-1)
    Payload += Author.SignedInt(-1)
    Payload += Author.SignedInt(ExtId)
    Payload += b"\xE2"
    Payload += b"\xE2" + Author.SignedInt(0) + Author.SignedInt(-1)
    return Payload


def MeasuredSketch(EntityCount: int = 0) -> bytes:
    Payload = Author.StructHeader("gsec_ptr") + b"\xF8\x01\xF7\x2A\xFB"
    Payload += b"\xE2"
    Payload += Author.FieldValue(1, "type", Author.SignedInt(2))
    Payload += Author.FieldValue(1, "is_ref_gsec", Author.SignedInt(0))
    Payload += Author.FieldValue(10, "name", b"Sketch 1\x00")
    Payload += Author.StructHeader("gsec2d_ptr") + b"\xE3"
    Payload += Author.StructHeader("segtab_ptr") + b"\xF8\x06\xF7\x2F\xFB"
    for IndexValue, (TypeValue, Dir, Points, ExtId, VerHor) in enumerate(
        KMeasuredSegments
    ):
        Payload += MeasuredSegment(
            TypeValue, Dir, Points, ExtId, VerHor, IndexValue == 0
        )
    Payload += b"\xE0\x01attributes\x00\xF0\x08\xF1\xF7\x3A"
    Payload += Author.StructHeader("dimtab_ptr") + b"\xF3\xF8\x04\xF7\x3E\xFB"
    for IndexValue, Value in enumerate(KDimensions):
        Payload += Dimension(Value, IndexValue)
        Payload += DimensionRef(IndexValue, (IndexValue + 1) % len(KMeasuredSegments))
    Payload += SolverTables(8, EntityCount)
    return Payload


def BuildMeasured(Source: Path, Target: Path, EntityCount: int = 0) -> bytes:
    DataValue = Source.read_bytes()
    Header = ReadHeader(DataValue)
    Element = b"\xE3"
    Element += Author.FieldValue(1, "id", Author.SignedInt(66))
    Element += Author.FieldValue(1, "symbol_key", Author.SignedInt(-1))
    Element += Author.FieldValue(1, "model_type", Author.SignedInt(2))
    Element += Author.StructHeader("group_info_ptr") + b"\xE1"
    Element += Author.StructHeader("place_rec_ptr") + Author.PlacementRecord()
    Element += Author.StructHeader("sub_feat_arr") + b"\xF8\x01\xF7\x17\xFB"
    Element += b"\xE3"
    Element += Author.FieldValue(1, "id", Author.SignedInt(0))
    Element += Author.FieldValue(1, "type", Author.SignedInt(160))
    Element += Author.FieldValue(1, "sub_type", Author.SignedInt(-1))
    Element += Author.StructHeader("data(subft_indexnumber)") + b"\xE3"
    Element += Author.FieldValue(1, "index", Author.SignedInt(1))
    Element += Author.FieldValue(1, "tool_type", Author.SignedInt(60001))
    Element += Author.FieldValue(1, "sep_index", Author.SignedInt(-1))
    Element += Author.StructHeader("expl_state_ref") + b"\xF3\xE1"
    Element += Author.StructHeader("feat_outl_info") + b"\xE3"
    Element += b"\xE0\x02ent_outl\x00\xF9\x02\x03" + Author.RunValues(KOutline)
    Element += Author.FieldValue(1, "max_text_len", Author.SignedInt(0))
    Element += Author.StructHeader("pre_roll_back") + b"\xE1"
    Element += Author.StructHeader("post_roll_back") + b"\xE1"
    Element += Author.StructHeader("post_regen") + b"\xE1"
    Element += Author.StructHeader("parchild_table") + b"\xF1\xE3"
    Element += b"\xE0\x09Structure_Invalid\x00" + Author.SignedInt(43981)
    Element += Author.StructHeader("copy_info_ptr") + b"\xF1\xE1"
    Element += Author.StructHeader("embed_info_ptr") + b"\xE1"
    Element += MeasuredSketch(EntityCount)
    Row = (
        Author.StructHeader("Sld_FeatDefs")
        + b"\xE3"
        + Author.StructHeader("feat_defs_949")
        + b"\xF8\x01\xF7\x02\xFB"
        + Element
        + Author.StructHeader("feat_defs_917")
        + b"\xF4\x06\xF8\x01\xF7\x80\xC4\xFB"
        + Author.SolidFeatureDefinition(74, (100.0,))
    )
    Result = Subset.Build(DataValue, Header.base, set(), {"FeatDefs": b"#FeatDefs\n" + Row})
    Target.write_bytes(Result)
    print(f"{Target.name}: {len(Result)} bytes; element {len(Element)}")
    return Result


def BuildSketchSwap(Source: Path, Target: Path) -> bytes:
    """Our element prefix with the vendor sketch and solver tail from gsec_ptr onward."""
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
    End = Payload.find(b"\xE0\x00feat_defs_917\x00")
    Vendor = Payload[37:End]
    Marker = b"\xE0\x00gsec_ptr\x00"
    Ours = FullElement(66)
    Swapped = Ours[: Ours.find(Marker)] + Vendor[Vendor.find(Marker) :]
    Row = (
        Author.StructHeader("Sld_FeatDefs")
        + b"\xE3"
        + Author.StructHeader("feat_defs_949")
        + b"\xF8\x01\xF7\x02\xFB"
        + Swapped
        + Author.StructHeader("feat_defs_917")
        + b"\xF4\x06\xF8\x01\xF7\x80\xC4\xFB"
        + Author.SolidFeatureDefinition(74, (100.0,))
    )
    Result = Subset.Build(DataValue, Header.base, set(), {"FeatDefs": b"#FeatDefs\n" + Row})
    Target.write_bytes(Result)
    print(f"{Target.name}: {len(Result)} bytes; swapped element {len(Swapped)}")
    return Result
