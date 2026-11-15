"""Research probe: emit a class-917 protrusion record with every declared field nulled.

Record 67 of the ladder — the first solid feature — declares 37 fields, all of them revision and reference
bookkeeping rather than geometry. This probe takes the proven four-record assembly (three datum planes and a
generated coordinate system), appends a 917 record built from that declared order with every field set to null
or `-1`, and rebuilds the loadable part that already carries a generated dimension.

It exists to answer one question: is a 917 accepted when its structure is right but it references no geometry?
The answer is no — see `re/creo/data-model/FeatureRecord.md`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "re/creo/tools")

import Subset
from convert.adapters.creo import Author
from convert.adapters.creo.Header import ReadHeader

KFields = (
    ("dtm_id_tab", 0),
    ("dtm_id", 1),
    ("dim_id", 1),
    ("comp_hist", 0),
    ("owner_id", 1),
    ("component_ids", 1),
    ("sorted", 1),
    ("revnums", 0),
    ("owner_type", 1),
    ("owner_ind", 1),
    ("ref_id", 1),
    ("owner_id", 1),
    ("hist_ref_info", 0),
    ("coll_refs_info", 0),
    ("ref_revnum", 1),
    ("ref_plcm_revnum", 1),
    ("ref_status", 1),
    ("dma_update_revnum", 1),
    ("flags_arr", 1),
    ("upd_ctrl_data", 0),
    ("upd_ref_revnum", 1),
    ("upd_coll_refs_info", 0),
    ("upd_aggr_rev_info", 0),
    ("rev_info_arr", 0),
    ("type", 1),
    ("info(basic_geom_rev_info)", 0),
    ("mdl_geom_rev", 0),
    ("type", 1),
    ("revision(mdl_g_rev_dtl_t_ft_regen)", 0),
    ("val", 0),
    ("rev_cnt", 1),
    ("tstamp", 0),
    ("version", 0),
    ("versions", 1),
    ("flags_arr", 1),
    ("aggr_rev_info", 0),
    ("aux_rev_data", 0),
)


def NullField(NameText: str, TypeDigit: int) -> bytes:
    if TypeDigit == 0:
        return Author.StructHeader(NameText) + b"\xE1"
    if TypeDigit == 10:
        return Author.FieldValue(10, NameText, b"\xE1")
    return Author.FieldValue(TypeDigit, NameText, Author.SignedInt(-1))


def Datum(FeatureId: int, ClassValue: int, NameText: str, GeomValue: int, Rev: int) -> bytes:
    return Author.DatumFeatureRecord(
        FeatureId,
        ClassValue,
        NameText,
        GeomValue,
        -5778,
        (-1,) * 252,
        200000,
        200001,
        1000000000,
        12345,
        99,
        Rev,
        1,
        3,
    )


def Section() -> bytes:
    Protrusion = Author.ReplayOf(Datum(67, 917, "PROTRUSION", -1, 1))
    Protrusion += b"".join(NullField(NameText, TypeDigit) for NameText, TypeDigit in KFields)
    Protrusion += b"\xF2"
    Payload = Author.StructHeader("Sld_Features") + b"\xE3"
    Payload += Author.StructHeader("first_feat_ptr") + b"\xE3"
    Payload += Datum(7, 923, "FRONT", 8, 3)
    Payload += Author.StructHeader("next_feat_ptr") + b"\xF2\xE3"
    Payload += b"\xF7\x03" + Author.ReplayOf(Datum(5, 923, "TOP", 6, 2))
    Payload += b"\xE3" + Author.ReplayOf(Datum(3, 923, "RIGHT", 4, 2))
    Payload += b"\xE3" + Author.CsysFeatureRecord(
        11, -5778, (-1,) * 252, 200000, 200001, 1000000000, 12345, 99, 0, 7, 3
    )
    Payload += b"\xE3" + Protrusion
    Payload += b"\xE1" + Author.LayerListTail(7)
    return Author.SectionValue("AllFeatur", Payload)


if __name__ == "__main__":
    Source = Path.home() / "Documents/creo-authored/featdefs.prt"
    DataValue = Source.read_bytes()
    Header = ReadHeader(DataValue)
    Result = Subset.Build(DataValue, Header.base, set(), {"AllFeatur": Section()})
    Target = Path.home() / "Documents/creo-authored/solid917b.prt"
    Target.write_bytes(Result)
    SectionValue = Section()
    print(f"{Target.name}: {len(Result)} bytes, AllFeatur {len(SectionValue)}")
