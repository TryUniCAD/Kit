from __future__ import annotations

from Dsl import base, cstr, emb, f64, i16, i32, u32
from AnnotationWire import current_19000
from defs.ConfigDetail import layer


def define(reg):
    reg.define(
        "moGeneralTableDefs_c",
        [
            current_19000(),
            i32("f2c"),
            i32("f28"),
            u32("f08"),
            i16("f0c"),
            layer("f0c", "f30"),
            i32("f38"),
            emb("f18", "utLineWidth_c.Serialize0"),
            emb("f20", "utLineWidth_c.Serialize0"),
            emb("f10", "utCharFormat_c"),
        ],
    )
    reg.define(
        "moRevisionTableDefs_c",
        [
            current_19000(),
            base("moGeneralTableDefs_c"),
            i32("f40"),
            i32("f44"),
            i32("f48"),
            u32("f58"),
            i32("f4c"),
            cstr("f50"),
        ],
    )
    reg.define(
        "moBOMTableDefs_c",
        [
            current_19000(),
            base("moGeneralTableDefs_c"),
            u32("f40"),
            cstr("f48"),
            cstr("f50"),
            cstr("f58"),
        ],
    )
    reg.define(
        "moTitleBlockTableDefs_c", [current_19000(), base("moGeneralTableDefs_c")]
    )
    reg.define(
        "moHoleTableDefs_c",
        [
            current_19000(),
            base("moGeneralTableDefs_c"),
            i32("f40"),
            i32("f44"),
            f64("f48"),
            f64("f50"),
            i32("f58"),
            i32("f5c"),
            i32("f60"),
            i32("f68"),
            i32("f6c"),
            i32("f70"),
            i32("f74"),
            i32("f78"),
            i32("f64"),
            i32("f7c"),
        ],
    )
    reg.define(
        "moWeldTableDefs_c", [current_19000(), base("moGeneralTableDefs_c"), i32("f40")]
    )
    reg.define(
        "moBendTableDefs_c",
        [
            current_19000(),
            base("moGeneralTableDefs_c"),
            i32("f40"),
            i32("f44"),
            i32("f4c"),
            i32("f48"),
        ],
    )
    reg.define(
        "moPunchTableDefs_c",
        [
            current_19000(),
            base("moGeneralTableDefs_c"),
            i32("f40"),
            i32("f44"),
            f64("f58"),
            f64("f60"),
            i32("f48"),
            i32("f4c"),
            i32("f6c"),
            i32("f50"),
            i32("f70"),
            i32("f68"),
        ],
    )
    reg.define(
        "moFamilyTableDefs_c",
        [current_19000(), base("moGeneralTableDefs_c"), u32("f40")],
    )
    reg.define(
        "moTableDefs_c",
        [
            current_19000(),
            i32("f08"),
            emb("f10", "moGeneralTableDefs_c"),
            emb("f50", "moRevisionTableDefs_c"),
            emb("fb0", "moBOMTableDefs_c"),
            emb("f150", "moHoleTableDefs_c"),
            emb("f328", "utCharFormat_c"),
            emb("f110", "moTitleBlockTableDefs_c"),
            emb("f1d0", "moWeldTableDefs_c"),
            emb("f218", "moBendTableDefs_c"),
            emb("f268", "moPunchTableDefs_c"),
            emb("f2e0", "moFamilyTableDefs_c"),
            f64("f330"),
            f64("f338"),
        ],
    )
