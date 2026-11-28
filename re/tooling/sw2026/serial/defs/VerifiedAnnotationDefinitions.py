from __future__ import annotations

from Dsl import base, cstr, emb, f64, i16, i32, u16, u32
from AnnotationWire import current_19000
from defs.ConfigDetail import layer


def define(reg):
    reg.define(
        "moBaseAnnotationDefs_c",
        [
            current_19000(),
            i32("f8"),
            f64("f10"),
            i32("f18"),
            i32("f1c"),
            i32("f20"),
            i32("f24"),
            i32("f34"),
            i32("f40"),
            i16("f44"),
            layer("f44", "f48"),
            emb("f2c", "utLineWidth_c.Serialize0"),
            emb("f38", "utLineWidth_c.Serialize0"),
            emb("f50", "utCharFormat_c"),
            i32("f28"),
        ],
    )
    reg.define(
        "moRevCloudDefs_c",
        [current_19000(), base("moBaseAnnotationDefs_c"), f64("f58")],
    )
    reg.define(
        "moWeldDefs_c",
        [
            current_19000(),
            base("moBaseAnnotationDefs_c"),
            i32("f58"),
            emb("f60", "utCharFormat_c"),
        ],
    )
    reg.define(
        "moSFDefs_c",
        [
            current_19000(),
            base("moBaseAnnotationDefs_c"),
            i32("f58"),
            i32("f5c"),
            f64("f60"),
            f64("f68"),
        ],
    )
    reg.define(
        "moBendNoteDefs_c",
        [
            current_19000(),
            base("moBaseAnnotationDefs_c"),
            i32("f58"),
            i32("f5c"),
            i32("f60"),
            f64("f68"),
        ],
    )
    reg.define(
        "moGtolDefs_c",
        [
            current_19000(),
            base("moBaseAnnotationDefs_c"),
            i32("f58"),
            i32("f5c"),
            u16("f60"),
        ],
    )
    reg.define(
        "moDatumDefs_c",
        [
            current_19000(),
            base("moBaseAnnotationDefs_c"),
            i32("f58"),
            i32("f68"),
            i32("f6c"),
            i32("f60"),
            i32("f64"),
            i32("f5c"),
        ],
    )
    reg.define(
        "moBalloonDefs_c",
        [
            current_19000(),
            base("moBaseAnnotationDefs_c"),
            i32("f58"),
            i32("f5c"),
            i32("f60"),
            i32("f64"),
            i32("f68"),
            i32("f6c"),
            cstr("f70"),
            cstr("f78"),
            u32("f80"),
            f64("f90"),
            f64("f88"),
            i32("fb4"),
            i32("fb8"),
            cstr("fc0"),
            f64("f98"),
            f64("fa0"),
            f64("fa8"),
            i32("fb0"),
        ],
    )
    reg.define(
        "moViewLocationLabelDefs_c",
        [
            current_19000(),
            base("moBaseAnnotationDefs_c"),
            i32("f58"),
            i32("f5c"),
            i32("f60"),
            i32("f64"),
            f64("f68"),
            i32("f70"),
            f64("f78"),
            i32("f74"),
        ],
    )
    reg.define(
        "moNoteDefs_c",
        [
            current_19000(),
            base("moBaseAnnotationDefs_c"),
            i32("f58"),
            i32("f5c"),
            i32("f60"),
            f64("f68"),
            f64("f70"),
            f64("f78"),
            i32("f80"),
        ],
    )
    reg.define(
        "moAnnotationDefs_c",
        [
            current_19000(),
            i32("f10"),
            f64("f08"),
            i32("f14"),
            i32("f1c"),
            i32("f20"),
            i32("f24"),
            i32("f28"),
            u32("f38"),
            i32("f2c"),
            i32("f30"),
            i32("f18"),
            i32("f34"),
            emb("f2c0", "moBalloonDefs_c"),
            emb("f418", "moNoteDefs_c"),
            emb("f250", "moDatumDefs_c"),
            emb("f1e8", "moGtolDefs_c"),
            emb("f108", "moSFDefs_c"),
            emb("fa0", "moWeldDefs_c"),
            emb("f178", "moBendNoteDefs_c"),
            emb("f4a0", "moBaseAnnotationDefs_c"),
            emb("f40", "moRevCloudDefs_c"),
            emb("f398", "moViewLocationLabelDefs_c"),
        ],
    )
