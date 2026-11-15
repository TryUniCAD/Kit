"""Research probe: which property of the creo layer tail is validated.

The accepted one-feature section keeps the control's 129-byte tail, which declares four layer entries for
feature ids 7, 5, 3 and 11 even though only one feature exists. The generated one-element tail is
rejected. This builds variants that change one property at a time so the rule can be named:

- `t4_same`: four entries, all carrying our own feature id
- `t1_replay`: one entry, written in replay form
- `t0`: count zero
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "re/creo/tools")

import Subset
from convert.adapters.creo import Author
from convert.adapters.creo.Header import ReadHeader

Source = Path("re/creo/oracle/empty/solid_start_part_mmks.prt").read_bytes()
Header = ReadHeader(Source)

Record = Author.DatumFeatureRecord(
    7, 923, "FRONT", 8, -5778, (-1,) * 252, 200000, 200001, 1000000000, 12345, 99, 3, 1, 3
)


def Head() -> bytes:
    return (
        Author.StructHeader("Sld_Features")
        + b"\xE3"
        + Author.StructHeader("first_feat_ptr")
        + b"\xE3"
        + Record
        + Author.StructHeader("next_feat_ptr")
        + b"\xE1"
    )


def Element(First: bool, FeatureId: int) -> bytes:
    Lead = b"" if First else b"\xF7\x51"
    return (
        Lead
        + b"\xE2"
        + (b"\xE0\x01feat_id\x00" if First else b"")
        + Author.SignedInt(FeatureId)
        + (b"\xE0\x01layer_id\x00" if First else b"")
        + b"\x00"
        + (b"\xE0\x01back_layer_id\x00" if First else b"")
        + b"\x00"
        + (b"\xF1" if First else b"")
    )


def Footer() -> bytes:
    return (
        Author.StructHeader("footer")
        + b"\xF2\xE3"
        + Author.StructHeader("foot_first_feat_ptr")
        + b"\xE1"
        + Author.FieldValue(1, "foot_layer_count", Author.SignedInt(0))
        + b"\xF2"
    )


def Tail(Count: int, Ids: tuple[int, ...]) -> bytes:
    Payload = Author.FieldValue(
        0, "layer_list", b"\xF8" + Author.CompactInt(Count) + b"\xF7\x51\xFB"
    )
    for IndexValue, FeatureId in enumerate(Ids):
        Payload += Element(IndexValue == 0, FeatureId)
    return Payload + Footer()


Variants = {
    "t4_same": Tail(4, (7, 7, 7, 7)),
    "t1_replay": Tail(1, (7,)),
    "t0": Tail(0, ()),
}

for Name, TailValue in Variants.items():
    Bodies = Author.EmptyPartSections((923, 979))
    Bodies["AllFeatur"] = Author.SectionValue("AllFeatur", Head() + TailValue)
    Target = Path.home() / "Documents/creo-authored" / f"{Name}.prt"
    Target.write_bytes(Subset.Build(Source, Header.base, set(), Bodies))
    print(f"{Name}: tail {len(TailValue)} bytes")
