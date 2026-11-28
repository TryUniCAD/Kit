from __future__ import annotations

from Dsl import base, cstr, emb, f64, i16, i32, u32
from AnnotationWire import current_19000
from defs.ConfigDetail import layer


def define(reg):
    reg.define(
        "moDrViewLabelData_c",
        [
            current_19000(),
            i32("f8"),
            i32("fc"),
            i32("f18"),
            i32("f14"),
            i32("f1c"),
            i32("f20"),
            i32("f24"),
            i32("f28"),
            i32("f44"),
            i32("f2c"),
            i32("f38"),
            i16("f48"),
            layer("f48", "f50"),
            cstr("f88"),
            cstr("f90"),
            u32("f5c"),
            i32("f10"),
            i32("f58"),
            emb("f98", "utCharFormat_c"),
            emb("fa0", "utCharFormat_c"),
            emb("f30", "utLineWidth_c.Serialize0"),
            emb("f3c", "utLineWidth_c.Serialize0"),
            emb("fa8", "utCharFormat_c"),
            emb("fb0", "utCharFormat_c"),
            emb("fb8", "utCharFormat_c"),
            emb("fc0", "utCharFormat_c"),
        ],
    )
    reg.define(
        "moDetailLabelData_c",
        [current_19000(), base("moDrViewLabelData_c"), u32("fcc"), i32("fc8")],
    )
    reg.define(
        "moSectionLabelData_c",
        [
            current_19000(),
            base("moDrViewLabelData_c"),
            f64("fc8"),
            f64("fd0"),
            f64("fd8"),
            i32("fe0"),
            i32("fe4"),
            i32("fec"),
            i32("ff0"),
            i32("fe8"),
        ],
    )
    reg.define(
        "moAuxLabelData_c", [current_19000(), base("moDrViewLabelData_c"), i32("fc8")]
    )
    reg.define(
        "moOrthoLabelData_c",
        [current_19000(), base("moDrViewLabelData_c"), i32("fc8"), i32("fcc")],
    )
    reg.define(
        "moMiscLabelData_c",
        [current_19000(), base("moDrViewLabelData_c"), i32("fc8"), i32("fcc")],
    )
    reg.define(
        "moLabelDefs_c",
        [
            current_19000(),
            i32("f8"),
            i32("fc"),
            emb("f18", "moDetailLabelData_c"),
            emb("fe8", "moSectionLabelData_c"),
            emb("f1e8", "moAuxLabelData_c"),
            emb("f458", "utCharFormat_c"),
            emb("f2b8", "moOrthoLabelData_c"),
            emb("f388", "moMiscLabelData_c"),
        ],
    )
