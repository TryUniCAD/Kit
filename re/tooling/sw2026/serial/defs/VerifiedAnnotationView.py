from __future__ import annotations

from Dsl import base, f64, i32, obj
from AnnotationWire import current_19000
from defs.ConfigPart import ObjShadow


def define(reg):
    reg.define(
        "moAnnotationView_c",
        [
            current_19000(),
            base("moView_c"),
            i32("f3d8"),
            obj("f3d0"),
            ObjShadow("f3e8", 0),
            i32("f3f0"),
            f64("f3e0"),
            obj("f3e8"),
            i32("f3f4"),
            i32("f3f8"),
            obj("f2f0"),
            i32("f3fc"),
            i32("f408"),
            i32("f400"),
            i32("f404"),
        ],
    )
