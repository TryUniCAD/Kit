from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, i32, u32, u8, i16, f32, f64, cstr, emb, base
from Schema import If, Op, Rep, run_load, run_store


def f3(name):
    return [f32(f"{name}_{k}") for k in range(3)]


class Present(Op):
    def __init__(self, flag, field, body):
        self.flag, self.field, self.body = flag, field, list(body)

    def load(self, ar, scope, o):
        v = ar.prim("i32")
        scope[self.flag] = v
        if v != 0:
            run_load(self.body, ar, scope, o)

    def store(self, ar, scope, o):
        on = self.field in getattr(scope, "own", scope)
        ar.prim("i32", 1 if on else 0)
        if on:
            run_store(self.body, ar, scope, o)


def define(reg):
    reg.provisional("uoMaterialTextureProperties.restore", [
        *[f64(f"f{8 * k + 8:02x}") for k in range(13)],
        cstr("f70"),
        i16("f78"),
        i32("f7c"),
        Vgt(0xF1D, [f64("f80"), f64("f88")]),
        Vgt(0x372A, [i32("f9c")]),
    ])
    reg.provisional("uoRVAppearanceProperties.restore", [
        u32("f00"),
        u32("f04"),
        cstr("f08"),
        u8("f10"),
        u32("f14"),
        *[f32(f"f{k:02x}") for k in range(0x18, 0x40, 4)],
        Vge(0x1052, [i32("f40"), f32("f44")]),
        Vgt(0x10A1, [f32("f48")]),
        Vgt(0x10BF, [f32("f4c"), f32("f50"), f32("f54"), i32("f58")]),
        Vge(0x1165, [
            f32("f5c"), f32("f60"), cstr("f68"), u32("f70"), f32("f74"), f32("f78"), cstr("f80"),
            f32("f88"), f32("f8c"), f32("f90"), i32("f9c"),
        ]),
        Vgt(0x1179, [f32("f94"), i32("fa0"), *[f32(f"f{k:02x}") for k in range(0xA4, 0xC4, 4)]]),
        Vgt(0x119E, [f32("fd0"), f32("fd4")]),
        Vgt(0x11AC, [f32("fd8")]),
        Vgt(0x1415, [f32("fdc"), f32("fe0")]),
        Vgt(0x1421, [cstr("fe8")]),
        Vgt(0x1462, [f32("f98")]),
        Vgt(0x3347, [Vlt(0x46BA, [
            cstr("old_a"), cstr("old_b"), cstr("old_c"),
            *[f32(f"old_f{k}") for k in range(17)],
            u32("old_u0"), u32("old_u1"), i32("old_i0"), i32("old_i1"), i32("old_i2"), i32("old_i3"),
        ])]),
    ])
    reg.provisional("moPropertyExt_c.restore", [
        u32("kind"),
        If(lambda s, ar: s["kind"] == 0, [f32("value")]),
        If(lambda s, ar: s["kind"] == 1, [i32("value")]),
        If(lambda s, ar: s["kind"] == 2, [cstr("value")]),
    ])
    reg.provisional("moUserProperty_c.restore", [
        u32("n"),
        Rep(lambda s, ar: s["n"] if s["n"] < 0x80000000 else 0, "props", [emb("p", "moPropertyExt_c.restore")]),
    ])
    reg.provisional("uoMaterialProperties.restore", [
        cstr("f28"),
        cstr("f20"),
        f64("f38"), f64("f40"), f64("f48"), f64("f50"),
        Vgt(0x172, [f64("f58"), f64("f60")]),
        Vgt(0x937, [Present("has_f80", "f80", [emb("f80", "uoMaterialTextureProperties.restore")])]),
        Vgt(0x954, [i32("f68"), i32("f6c"), i32("f70"), i32("f74"), i32("f78")]),
        Vgt(0xA05, [cstr("f30")]),
        Vgt(0xDB3, [i32("f7c")]),
        Vgt(0xF1D, [Present("has_f90", "f90", [emb("f90", "uoRVAppearanceProperties.restore")])]),
        Vgt(0x3368, [cstr("fb8")]),
        Vgt(0x372A, [Present("has_f98", "f98", [emb("f98", "uoMaterialTextureProperties.restore")])]),
        emb("user", "moUserProperty_c.restore"),
    ])
    reg.provisional("uoDSPBRProperties_c.restore", [
        *f3("f10"),
        *[f32(n) for n in ("f28", "f2c", "f38", "f3c", "f50", "f54", "f48", "f98", "fd4", "f12c", "f60")],
        *f3("f64"),
        f32("f7c"),
        *f3("f70"),
        f32("ff8"),
        *f3("fb8"),
        f32("fc4"),
        i32("fcc"),
        f32("fa8"),
        f32("fac"),
        *f3("f9c"),
        f32("f80"),
        f32("f90"),
        f32("f94"),
        *f3("f84"),
        f32("fe8"),
        *f3("fdc"),
        *f3("fec"),
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
            *f3("f108"),
            cstr("f118"),
            cstr("f120"),
        ]),
        Vgt(0x4971, [f32("f158"), f32("f15c"), cstr("f140"), cstr("f148"), cstr("f150")]),
    ])
    reg.provisional("moVisualProperties_c.restore", [
        Vgt(0x90, [u32("f0c")]),
        Vgt(0xD3, [u32("f14")]),
        Vgt(0xAC, [u32("f18")]),
        emb("f20", "uoMaterialProperties.restore"),
        Vgt(0xB2B, [cstr("f40"), i32("f48")]),
        Vgt(0xB53, [i32("f4c")]),
        Vgt(0xB55, [cstr("f50")]),
        Vgt(0xDB1, [i32("f58")]),
        Vgt(0x1051, [i32("f5c")], [Vge(0xE55, [i32("old_f5c")])]),
        Vgt(0x144B, [i32("f78")]),
        Vgt(0x2419, [i32("f7c")]),
        Vgt(0x2794, [i32("f80")]),
        Vgt(0x3F08, [Present("has_f88", "f88", [emb("f88", "uoDSPBRProperties_c.restore")])]),
    ])
    reg.provisional("moVisualProperties_c", [base("moVisualProperties_c.restore")])
