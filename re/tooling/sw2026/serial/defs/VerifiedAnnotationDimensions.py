from __future__ import annotations

from Dsl import base, cstr, emb, f64, i16, i32, u32
from AnnotationWire import current_19000
from defs.ConfigDetail import layer


def define(reg):
    reg.define(
        "moBaseDimDef_c",
        [
            current_19000(),
            i32("f08"),
            i32("fc"),
            i32("f10"),
            f64("f18"),
            f64("f20"),
            i32("f28"),
            f64("f30"),
            f64("f38"),
            i32("f40"),
            i32("f44"),
            cstr("f48"),
            cstr("f50"),
            f64("f58"),
            f64("f60"),
            i32("f68"),
            i32("f6c"),
            i32("f70"),
            i32("f74"),
            i32("f80"),
            i32("f84"),
            i32("f88"),
            i32("f8c"),
            i16("f90"),
            i32("f94"),
            i32("f98"),
            u32("fe0"),
            layer("f90", "fa0"),
            emb("ff0", "moLengthUserUnits_c"),
            emb("ff8", "moAngleUserUnits_c"),
            emb("fe8", "utCharFormat_c"),
            emb("fd0", "uiLFConfig_c"),
            emb("fd8", "uiLFConfig_c"),
            i32("fc0"),
            i32("f78"),
            i32("f9c"),
        ],
    )
    reg.define(
        "moLinearDimDef_c",
        [
            current_19000(),
            base("moBaseDimDef_c"),
            u32("f108"),
            i32("f100"),
            i32("f104"),
        ],
    )
    reg.define(
        "moAngleDimDef_c", [current_19000(), base("moBaseDimDef_c"), u32("f100")]
    )
    reg.define("moArcLengthDimDef_c", [current_19000(), base("moBaseDimDef_c")])
    reg.define(
        "moRadialDimDef_c",
        [current_19000(), base("moBaseDimDef_c"), u32("f100"), i32("f104")],
    )
    reg.define(
        "moHoleCalloutDimDef_c", [current_19000(), base("moBaseDimDef_c"), u32("f100")]
    )
    reg.define(
        "moOrdinateDimDef_c",
        [
            current_19000(),
            base("moBaseDimDef_c"),
            i32("f100"),
            u32("f104"),
            f64("f108"),
        ],
    )
    reg.define(
        "moAngOrdinateDimDef_c",
        [
            current_19000(),
            base("moBaseDimDef_c"),
            i32("f100"),
            u32("f104"),
            i32("f108"),
            i32("f110"),
            i32("f114"),
        ],
    )
    reg.define(
        "moChamferDimDef_c",
        [
            current_19000(),
            base("moBaseDimDef_c"),
            i32("f100"),
            i32("f104"),
            i32("f108"),
            i32("f10c"),
            f64("f118"),
            f64("f120"),
            i32("f110"),
            i32("f128"),
        ],
    )
    reg.define(
        "moDiameterDimDef_c",
        [current_19000(), base("moBaseDimDef_c"), i32("f100"), u32("f104")],
    )
    reg.define(
        "moDimDefs_c",
        [
            current_19000(),
            i32("f68"),
            f64("f8"),
            f64("f10"),
            f64("f18"),
            f64("f20"),
            f64("f28"),
            f64("f30"),
            f64("f38"),
            f64("f40"),
            f64("f48"),
            f64("f50"),
            f64("f58"),
            i32("f60"),
            i32("f64"),
            i32("f6c"),
            i32("f70"),
            i32("f74"),
            f64("f78"),
            f64("f80"),
            i32("f88"),
            i32("f8c"),
            f64("f90"),
            f64("f98"),
            f64("fa0"),
            u32("fd8"),
            i32("fa8"),
            f64("fb0"),
            i32("fb8"),
            i32("fbc"),
            i32("fc0"),
            i32("fc4"),
            i32("fd0"),
            i32("fd4"),
            i32("fcc"),
            emb("fe0", "moLinearDimDef_c"),
            emb("f1f0", "moAngleDimDef_c"),
            emb("f2f8", "moArcLengthDimDef_c"),
            emb("f3f8", "moRadialDimDef_c"),
            emb("f500", "moHoleCalloutDimDef_c"),
            emb("f608", "moOrdinateDimDef_c"),
            emb("f830", "moChamferDimDef_c"),
            emb("f960", "moDiameterDimDef_c"),
            emb("f718", "moAngOrdinateDimDef_c"),
            emb("fa68", "moBaseDimDef_c"),
        ],
    )
