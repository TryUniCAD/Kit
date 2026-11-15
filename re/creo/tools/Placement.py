"""Research probe: a Creo feature definition with its placement record.

`Author.DefaultFeatDefs` writes a ten-field definition whose `place_rec_ptr` is null. The ladder's own
definitions nest a placement record there — `local_sys` (12 doubles), `own_ref_id`, `orient`, `trf_arr` (one
element of `type`/`key`/`idx`), `transf` (12 doubles), then `plcm_revnum`, `next_prop`, `cond_tbl_idx`,
`comment`, `merge_info_ptr`, `state_ind` and `alumni_info` — and then the `dimtab_ptr` dimension table.

This probe emits that richer shape so two questions can be answered by measurement rather than inference:

- does the datum-only control still load with placement records present (a regression check), and
- does the ladder's container stop crashing once its definitions carry placements.

Vendor files are research oracles and are never shipped.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "re/creo/tools")

import AddRow
import Subset
from convert.adapters.creo import Author
from convert.adapters.creo.Header import ReadHeader

# an identity frame, as the ladder stores it for a feature that is not transformed
KIdentity = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)


# the ladder writes these frames as the f9 04 03 double array with run compression
def MatrixValue(Values: tuple[float, ...]) -> bytes:
    return b"\xF9\x04\x03" + Author.RunValues(Values)


def PlacementRecord() -> bytes:
    Payload = b"\xE3"
    Payload += b"\xE0\x02local_sys\x00" + MatrixValue(KIdentity)
    Payload += Author.FieldValue(1, "own_ref_id", Author.SignedInt(-1))
    Payload += Author.FieldValue(1, "orient", Author.SignedInt(0))
    Payload += Author.StructHeader("trf_arr") + b"\xF8\x01\xF7\x0B\xFB"
    Payload += b"\xE3"
    Payload += Author.FieldValue(1, "type", Author.SignedInt(1))
    Payload += Author.FieldValue(1, "key", Author.SignedInt(-1))
    Payload += Author.FieldValue(1, "idx", Author.SignedInt(0))
    Payload += b"\xE0\x02transf\x00" + MatrixValue(KIdentity)
    Payload += Author.StructHeader("plcm_revnum") + b"\xF2\xE1"
    Payload += Author.StructHeader("next_prop") + b"\xF1\xE1"
    Payload += Author.FieldValue(1, "cond_tbl_idx", Author.SignedInt(-1))
    Payload += Author.FieldValue(10, "comment", b"\xE1")
    Payload += Author.StructHeader("merge_info_ptr") + b"\xE1"
    Payload += Author.FieldValue(1, "state_ind", Author.SignedInt(-1))
    Payload += Author.StructHeader("alumni_info") + b"\xE1"
    return Payload


def DefinitionBlock(
    FeatureId: int, DimensionValue: tuple[float, ...] = (100.0,)
) -> bytes:
    Payload = b"\xE2"
    Payload += Author.FieldValue(1, "id", Author.SignedInt(FeatureId))
    Payload += Author.FieldValue(1, "symbol_key", Author.SignedInt(-1))
    Payload += Author.FieldValue(1, "model_type", Author.SignedInt(2))
    Payload += Author.StructHeader("group_info_ptr") + b"\xE1"
    Payload += Author.StructHeader("place_rec_ptr") + PlacementRecord()
    Payload += Author.FieldValue(
        0,
        "dimtab_ptr",
        b"\xF8" + Author.CompactInt(len(DimensionValue)) + b"\xF7\x03\xFB",
    )
    for Value in DimensionValue:
        Payload += b"\xE2"
        Payload += Author.FieldValue(1, "type", Author.SignedInt(1))
        Payload += Author.FieldValue(2, "value", Author.ScalarValue(Value))
        Payload += Author.FieldValue(1, "direct", Author.SignedInt(-1))
        Payload += Author.FieldValue(2, "aux_value", Author.ScalarValue(Value))
        Payload += Author.FieldValue(1, "ext_id", Author.SignedInt(-1))
        Payload += Author.FieldValue(0, "dispdimattr", Author.SignedInt(0))
        Payload += Author.FieldValue(1, "dimattr", Author.SignedIntArray((0,) * 7))
        Payload += b"\xF2"
    return Payload


def FeatDefs(
    DimensionValue: tuple[float, ...] = (100.0,),
    FeatureIds: tuple[int, ...] = (7,),
) -> bytes:
    Payload = Author.StructHeader("Sld_FeatDefs") + b"\xE3"
    Payload += Author.StructHeader("feat_defs_949")
    Payload += b"\xF8" + Author.CompactInt(len(FeatureIds)) + b"\xF7\x02\xFB"
    for Value in FeatureIds:
        Payload += DefinitionBlock(Value, DimensionValue)
    return Payload


def Build(Source: Path, FeatureIds: tuple[int, ...], Target: Path) -> bytes:
    DataValue = Source.read_bytes()
    Header = ReadHeader(DataValue)
    Present = {
        Entry.name
        for TableValue in Subset.ReadTables(DataValue, Header.base)
        for Entry in TableValue.rows
    }
    if "FeatDefs" not in Present:
        Row = None
        for TableValue in Subset.ReadTables(DataValue, Header.base):
            for Entry in TableValue.rows:
                if Entry.name == "EMPTY_SPACE_FOR_REUSE" and Entry.length == 157:
                    Row = Entry
        if Row is None:
            raise SystemExit("the reserved 157-byte row was not found")
        DataValue = AddRow.RenameRow(DataValue, Row, "FeatDefs")
        Header = ReadHeader(DataValue)
    Body = Author.SectionValue("FeatDefs", FeatDefs((100.0, 42.5), FeatureIds))
    Result = Subset.Build(DataValue, Header.base, set(), {"FeatDefs": Body})
    Target.write_bytes(Result)
    print(f"{Target.name}: {len(Result)} bytes, FeatDefs body {len(Body)}, ids {FeatureIds}")
    return Result


if __name__ == "__main__":
    Home = Path.home() / "Documents/creo-authored"
    Build(
        Path("re/creo/oracle/empty/solid_start_part_mmks.prt"),
        (7, 5, 3, 11),
        Home / "place_ctrl.prt",
    )
    Build(
        Path("re/creo/oracle/ladder/ladder1.prt.2"),
        (7, 5, 3, 11, 67, 75, 74),
        Home / "place_ladder.prt",
    )
