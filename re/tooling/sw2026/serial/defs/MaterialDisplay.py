from __future__ import annotations

from Core import ArchiveError
from Dsl import Vge, Vgt, Vlt, base, cstr, emb, f32, f64, i16, i32, obj, u8, u16, u32, ver
from Schema import Fn, If, Rep
from defs.ResolvedCore import Legacy, has_condition, obarray, xo


def flag(name):
    return lambda scope, archive: scope[name] != 0


def positive_count(name):
    return lambda scope, archive: max(scope[name], 0)


def floats3(name):
    return [f32(f"{name}_{index}") for index in range(3)]


def array_pointer(name):
    return [i32(f"has_{name}"), If(flag(f"has_{name}"), [obarray(name)])]


def require_display_context(archive, scope, obj):
    if ver(archive) != 19000:
        raise ArchiveError(f"display archive owners require version 19000, got {ver(archive)}")
    if has_condition(archive, 1 | 0x10000000):
        raise ArchiveError("display archive owners exclude location and alternate linked-object modes")


def define(reg):
    reg.define("PWMaterialManager_c.restore", [
        i32("f08"),
        i32("f0c"),
        emb("list", "suObList"),
    ])
    reg.define("uoModelData_c.restore", [
        Vgt(0x99, [
            Vlt(0x17D, [Legacy("uoModelData_c lights before 0x17d")]),
            obj("f08"),
        ]),
        Vgt(0x1BD, [i32("f10")]),
    ])
    reg.define("uoDSPBRProperties_c.restore", [
        *floats3("f10"),
        *[f32(name) for name in ("f28", "f2c", "f38", "f3c", "f50", "f54", "f48", "f98", "fd4", "f12c", "f60")],
        *floats3("f64"),
        f32("f7c"),
        *floats3("f70"),
        f32("ff8"),
        *floats3("fb8"),
        f32("fc4"),
        i32("fcc"),
        f32("fa8"),
        f32("fac"),
        *floats3("f9c"),
        f32("f80"),
        f32("f90"),
        f32("f94"),
        *floats3("f84"),
        f32("fe8"),
        *floats3("fdc"),
        *floats3("fec"),
        i32("fd0"),
        f32("f4c"),
        f32("fd8"),
        cstr("f20"),
        cstr("f40"),
        cstr("f30"),
        cstr("f58"),
        cstr("f08"),
        f32("f128"),
        Vgt(0x46B4, [
            cstr("f00"),
            cstr("fb0"),
            i32("fc8"),
            f32("ffc"),
            f32("f100"),
            f32("f104"),
            *floats3("f108"),
            cstr("f118"),
            cstr("f120"),
        ]),
        Vgt(0x4971, [f32("f158"), f32("f15c"), cstr("f140"), cstr("f148"), cstr("f150")]),
    ])
    reg.define("utLineWidth_c.Serialize.3.0", [
        Vge(0xF41, [i16("f06"), f32("f00")], [i32("f06")]),
    ])
    reg.define("utLineWidth_c.Serialize0", [
        Vge(0xF41, [i16("f06"), f32("f00")]),
    ])
    reg.define("moLineViz_c.Serialize.0", [
        cstr("f08"),
        emb("lw", "utLineWidth_c.Serialize.3.0"),
        i32("f10"),
        Vge(0xA80, [i32("f14")]),
    ])
    reg.define("moDisplayObject_c.FUN_4ba4d3c0", [
        Fn(require_display_context, require_display_context),
        u16("f50"),
        xo("f30"),
        xo("f40", "moDrView"),
        xo("f48", "moCompRef_c"),
        i32("f54"),
        i32("f11c"),
        emb("f08", "moEntVisProp_c"),
        emb("f68", "rf.suObList"),
        emb("fb0", "rf.suObList"),
        i32("f58"),
        xo("ff8", "moLinkedDispObjArray_c"),
        i32("linked"),
        If(flag("linked"), [
            i32("n138"),
            If(lambda scope, archive: scope["n138"] >= 1, [emb("f138", "rf.suObList")]),
        ]),
        i32("f118"),
    ])
    reg.define("moDisplayItem_c.Serialize", [
        Fn(require_display_context, require_display_context),
        base("moDisplayObject_c.FUN_4ba4d3c0"),
        i32("f390"),
        i32("f3e0"),
        emb("f290", "mgPoint_c.restore"),
        *array_pointer("f298"),
        i32("has_f288"),
        If(flag("has_f288"), [emb("f288", "rf.suObList")]),
        xo("f3f8", "moCompFeature_c"),
        emb("f400", "mgVector_c.restore"),
        emb("f2a0", "mgXform_c.restore"),
        i32("n2b0"),
        Rep(positive_count("n2b0"), "f2b0", [i32("v")]),
        u8("has_f2c0"),
        If(flag("has_f2c0"), [emb("f2c0", "mgVector_c.restore")]),
        f64("f2c8"),
        i32("has_f2d0"),
        If(flag("has_f2d0"), [emb("f2d0", "mgXform_c.restore")]),
        i32("n3d0"),
        Rep(positive_count("n3d0"), "f3c0", [xo("o")]),
        xo("f2d8"),
        f64("f3b8"),
        u32("n2e8"),
        Rep("n2e8", "f2e0", [i32("k"), xo("v", "moArrowSize_c")]),
        i32("f2f0"),
        emb("f2f8", "utLineWidth_c.Serialize.3.0"),
        i32("f2f4"),
        i32("f304"),
        emb("f30c", "utLineWidth_c.Serialize.3.0"),
        i32("f308"),
        i32("f300"),
        i32("f314"),
        i32("f334"),
        i32("f338"),
        *array_pointer("f4a0"),
        i32("f318"),
        i32("f31c"),
        emb("f320", "utLineWidth_c.Serialize0"),
        i32("f328"),
        i32("f32c"),
        u32("n4a8"),
        Rep("n4a8", "f4a8", [i32("k"), xo("v", "moSplineLeaderData_c")]),
        i32("has_f4b8"),
        If(flag("has_f4b8"), [Legacy("moWatermarkNoteData_c::Serialize")]),
        i32("n4f0"),
        If(lambda scope, archive: scope["n4f0"] < 5, [
            Rep(positive_count("n4f0"), "f4f0", [emb("p", "mgPoint_c.restore")]),
            i32("n550"),
            If(lambda scope, archive: scope["n550"] < 3, [
                Rep(positive_count("n550"), "f550", [emb("v", "mgVector_c.restore")]),
            ], [Legacy("moDisplayItem_c vector count >= 3")]),
        ], [Legacy("moDisplayItem_c point count >= 5")]),
    ])
