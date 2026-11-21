from __future__ import annotations

from Dsl import cstr, f32, f64, i32, u32
from AnnotationWire import current_19000


def define(reg):
    reg.define(
        "utCharFormat_c",
        [
            current_19000(),
            cstr("f08"),
            f64("f10"),
            i32("f18"),
            f64("f20"),
            u32("f30"),
            f64("f28"),
            f64("f38"),
            f64("f40"),
            f64("f48"),
            f64("f50"),
            u32("f58"),
        ],
    )
    reg.define(
        "utLineWidthPrintData_c",
        [
            current_19000(),
            f32("f8"),
            f32("fc"),
            f32("f10"),
            f32("f14"),
            f32("f18"),
            f32("f1c"),
            f32("f20"),
            f32("f24"),
        ],
    )
