from __future__ import annotations

from Core import ArchiveError
from Dsl import Vgt, Vge, Vlt, ver, i32, u32, u16, i16, u8, f64, f32, u64, obj, cstr, time32, rep, emb, base, count
from Schema import Op, If
from defs.ResolvedCore import vt, concept_vt, CONCEPT_LW, FEATURE_XML

PLANS = {
    "Contents/CMgr": ("rooted", 1),
}


class CondBit(Op):
    def __init__(self, mask, on):
        self.mask, self.on = mask, on

    def apply(self, ar):
        flags = ar.ctx.get("conditions", 0)
        ar.ctx["conditions"] = flags | self.mask if self.on else flags & ~self.mask

    def load(self, ar, scope, o):
        self.apply(ar)

    def store(self, ar, scope, o):
        self.apply(ar)


class Unmodelled(Op):
    def __init__(self, what):
        self.what = what

    def load(self, ar, scope, o):
        raise ArchiveError(f"unmodelled {self.what} at {ar.p}")

    def store(self, ar, scope, o):
        raise ArchiveError(f"unmodelled {self.what}")


class CtxSet(Op):
    def __init__(self, key, value):
        self.key, self.value = key, value

    def load(self, ar, scope, o):
        ar.ctx[self.key] = self.value

    def store(self, ar, scope, o):
        ar.ctx[self.key] = self.value


def ctx_on(key):
    return lambda s, ar: bool(ar.ctx.get(key, 0))


def With87c(body):
    return [CtxSet("ctx87c", 1), *body, CtxSet("ctx87c", 0)]


def With200(body):
    return [CondBit(0x200, True), *body, CondBit(0x200, False)]


def Vin(lo, hi, body):
    return If(lambda s, ar: lo < ver(ar) < hi, body)


def has_cond(ar, mask):
    return (ar.ctx.get("conditions", 0) & mask) != 0


def pos(name):
    return lambda s, ar: max(0, s[name])


def wide(hi, lo):
    return lambda s, ar: ((s[hi] & 0xFFFFFFFF) << 32) | (s[lo] & 0xFFFFFFFF)


def Flag(name, body, kind=u32):
    return [kind(name), If(lambda s, ar: s[name] != 0, body)]


def keyed_objs(count, name):
    return [u32(count), rep(count, name, [i32("key"), obj("o")])]


def int_pairs(count, name, second=i32):
    return [u32(count), rep(count, name, [i32("a"), second("b")])]


def define(reg):
    reg.provisional("mgVector_c.restore", [f64("x"), f64("y"), f64("z")])
    reg.provisional("mgPlane_c.restore", [f64("f08"), f64("f10"), f64("f18"), f64("f20"), f64("f28"), f64("f30")])
    reg.provisional("su_CMapStringToInt", [count("n"), rep("n", "items", [cstr("k"), i32("v")])])

    reg.define("moNodeName_c", [cstr("f08")])
    reg.define("moCustomPropertyList", [i32("n"), rep(pos("n"), "items", [emb("p", "moCustomProperty")])])
    reg.define("moCustomProperty", [
        cstr("f08"),
        cstr("f10"),
        cstr("f18"),
        Vge(0x8F5, [i32("f2c")]),
        Vge(0xADF, [u32("f28")]),
        Vgt(0x12C6, [cstr("f20")]),
        Vge(0x17F2, [i32("f34")]),
        Vge(0x1822, [i32("f38")]),
        Vgt(0x186D, [i32("f3c")]),
    ])
    reg.define("moSwiftSchemaRef_c", [cstr("f08"), i32("f10")])
    reg.define("moFaceColorConfig_c", With200([obj("f10"), obj("f18"), Vgt(0x7EC, [i32("f08")])]))

    reg.define("moUserProperty_c.restore", [
        i32("n"),
        rep(pos("n"), "props", [
            u32("kind"),
            If(lambda s, ar: s["kind"] == 0, [f32("v")]),
            If(lambda s, ar: s["kind"] == 1, [i32("v")]),
            If(lambda s, ar: s["kind"] == 2, [cstr("v")]),
        ]),
    ])
    reg.define("uoMaterialTextureProperties.restore", [
        *[f64(f"f{0x08 + 8 * k:02x}") for k in range(13)],
        cstr("f70"),
        i16("f78"),
        i32("f7c"),
        Vgt(0xF1D, [f64("f80"), f64("f88")]),
        Vgt(0x372A, [i32("f9c")]),
    ])
    reg.define("uoRVAppearanceProperties.restore", [
        u32("f00"),
        u32("f04"),
        cstr("f08"),
        u8("f10"),
        u32("f14"),
        *[f32(f"f{0x18 + 4 * k:02x}") for k in range(10)],
        Vlt(0x1052, [], [i32("f40"), f32("f44")]),
        Vgt(0x10A1, [f32("f48")]),
        Vgt(0x10BF, [f32("f4c"), f32("f50"), f32("f54"), i32("f58")]),
        Vlt(0x1165, [], [
            f32("f5c"), f32("f60"), cstr("f68"), u32("f70"), f32("f74"), f32("f78"),
            cstr("f80"), f32("f88"), f32("f8c"), f32("f90"), i32("f9c"),
        ]),
        Vgt(0x1179, [f32("f94"), i32("fa0"), *[f32(f"f{0xa4 + 4 * k:02x}") for k in range(8)]]),
        Vgt(0x119E, [f32("fd0"), f32("fd4")]),
        Vgt(0x11AC, [f32("fd8")]),
        Vgt(0x1415, [f32("fdc"), f32("fe0")]),
        Vgt(0x1421, [cstr("fe8")]),
        Vgt(0x1462, [f32("f98")]),
        Vgt(0x3347, [Vlt(0x46BA, [
            cstr("s0"), cstr("s1"), cstr("s2"),
            *[f32(f"g{k}") for k in range(17)],
            u32("u0"), u32("u1"), i32("i0"), i32("i1"), i32("i2"), i32("i3"),
        ])]),
    ])
    reg.define("uoMaterialProperties.restore", [
        cstr("f28"),
        cstr("f20"),
        f64("f38"), f64("f40"), f64("f48"), f64("f50"),
        Vgt(0x172, [f64("f58"), f64("f60")]),
        Vgt(0x937, Flag("has80", [emb("f80", "uoMaterialTextureProperties.restore")], i32)),
        Vgt(0x954, [i32("f68"), i32("f6c"), i32("f70"), i32("f74"), i32("f78")]),
        Vgt(0xA05, [cstr("f30")]),
        Vgt(0xDB3, [i32("f7c")]),
        Vgt(0xF1D, Flag("has90", [emb("f90", "uoRVAppearanceProperties.restore")], i32)),
        Vgt(0x3368, [cstr("fb8")]),
        Vgt(0x372A, Flag("has98", [emb("f98", "uoMaterialTextureProperties.restore")], i32)),
        emb("props", "moUserProperty_c.restore"),
    ])
    reg.define("moVisualProperties_c.restore", [
        Vgt(0x90, [u32("f0c")]),
        Vgt(0xD3, [u32("f14")]),
        Vgt(0xAC, [u32("f18")]),
        emb("f20", "uoMaterialProperties.restore"),
        Vgt(0xB2B, [cstr("f40"), i32("f48")]),
        Vgt(0xB53, [i32("f4c")]),
        Vgt(0xB55, [cstr("f50")]),
        Vgt(0xDB1, [i32("f58")]),
        If(lambda s, ar: ver(ar) < 0xE55 or ver(ar) > 0x1051, [Vgt(0x1051, [i32("f5c")])], [i32("old_5c")]),
        Vgt(0x144B, [i32("f78")]),
        Vgt(0x2419, [i32("f7c")]),
        Vgt(0x2794, [i32("f80")]),
        Vgt(0x3F08, Flag("has88", [emb("f88", "uoDSPBRProperties_c.restore")], i32)),
    ])
    reg.define("moVisualProperties_c", [base("moVisualProperties_c.restore")])

    reg.define("moMassProp_c", [
        f64("f20"), f64("f28"), f64("f30"), f64("f10"), f64("f08"), f64("f18"),
        f64("f38"), f64("f40"), f64("f48"), f64("f50"), f64("f60"), f64("f58"),
        Vgt(0x7D6, [i32("f1c0")]),
        Vgt(0x85C, [i32("f1c4")]),
        Vgt(0xA16, [i32("f1c8")]),
        Vgt(0xA97, [i32("f1cc")]),
        Vgt(0x10F0, [i32("f1e0")]),
        Vgt(0x116A, [Vlt(0x11D4, [f64("old0"), f64("old1"), f64("old2")])]),
        Vgt(0x11D5, [f64("f00")]),
        Vgt(0x13FA, [i32("f134"), i32("f138"), i32("f13c"), i32("f140"), cstr("f148"), cstr("f150")]),
        Vge(0x13FF, [
            i32("f1f0"),
            Vgt(0x1459, [
                f64("fc8"), f64("fd0"), f64("fd8"),
                Vgt(0x1460, [
                    emb("f68", "mgVector_c.restore"),
                    emb("f80", "mgVector_c.restore"),
                    emb("f98", "mgVector_c.restore"),
                    Vgt(0x1470, [i32("f15c"), Vgt(0x1FB5, [u16("f128")])]),
                ]),
            ]),
        ]),
    ])

    reg.define("moLinkedAtomIdNode_c", [
        i32("f08"),
        emb("f90", "su_CDWordArray"),
        emb("fd0", "su_CDWordArray"),
        *[op for k in ("f0", "100", "110", "120") for op in keyed_objs(f"n{k}", f"f{k}")],
    ])

    reg.define("mo3DPrintSettings_c.load", [
        f64("f08"), f64("f10"), f64("f18"), f64("f20"), i32("f28"), obj("f00"),
    ])

    reg.define("moPartConfigObject_c", [
        i32("f0c"),
        Vlt(0x3B3, [obj("old_owner")], [i32("f08")]),
        Vgt(0x643, [obj("fb0")]),
        Vgt(0x64A, [obj("fb8")]),
        Vlt(0x73E, [Vgt(0x735, [i32("old_a"), i32("old_b")])]),
        Vgt(0x73B, [Vlt(0x74E, With200([obj("old_featdata")]))]),
        Vgt(0xEE, [emb("f10", "suObList")]),
        Vgt(0x449, [emb("f60", "suObList")]),
        Vgt(0x1293, [emb("f100", "suObList")]),
        Vgt(0x119D, [emb("f80", "suObList")]),
        Vgt(0x67E, [emb("f68", "suObList")]),
        Vgt(0x74D, With200([emb("f58", "suObList")])),
        Vgt(0x8D1, With200([emb("f78", "suObList")])),
        *With200([Vgt(0x995, [
            *Flag("has_c8", [emb("fc8", "moBodyChooser_c")], u16),
            *Flag("has_d0", [emb("fd0", "moBodyChooser_c")], u16),
        ])]),
        Vgt(0x1192, With200(Flag("has_e0", [emb("fe0", "mConfigScaleFactor")], u16))),
        Vgt(0x1199, With200(Flag("has_e8", [emb("fe8", "mConfigCosmeticThread")], u16))),
        Vgt(0x11A9, With200(Flag("has_f0", [emb("ff0", "moConfigLimitMate")], u16))),
        Vgt(0xA0C, [emb("f70", "suObList")]),
        Vgt(0x11AD, [i32("fd8")]),
        Vgt(0x11DE, [i32("ff8")]),
        Vgt(0x1C05, Flag("has_98", [emb("f98", "suObList")], u16)),
        Vgt(0x2390, [obj("fa0")]),
        Vgt(0x2B8A, [obj("f88")]),
        Vgt(0x4972, [obj("fa8")]),
    ])

    reg.define("moBaseConfiguration_c", [
        Vlt(0x247, [], [base("moFeature_c")]),
        Vlt(0x3B3, [obj("old_owner")]),
        Vgt(0xA88, [If(lambda s, ar: bool(ar.ctx.get("doc_storage", 0)), [Unmodelled("archive helper +0x38 vt 0x5a8")])]),
        Vlt(0x247, [cstr("old_name")]),
        cstr("f4a8"),
        Vgt(0x1D0, [i32("f4b0")]),
        Vgt(0x1DD, [Vlt(0x3B3, [i32("old_1dd")])]),
        Vgt(0x260, [u32("f4c4"), cstr("f498")]),
        Vgt(0x26C, [Vlt(0x3B3, [emb("old_box", "mgBBox_c.restore")])]),
        Vlt(0x3B3, [], [u32("f85c")]),
        Vgt(0x53C, [u32("f860")]),
        Vgt(0x841, [Vlt(0x85D, [u8("old_841")])]),
        Vlt(0x496, [], [u32("f670"), emb("f668", "moMassProp_c")]),
        Vlt(0x4C8, [], [time32("f678")]),
        Vgt(0x539, [Vlt(0x718, [obj("old_vis")])]),
        Vgt(0x73B, [Vlt(0xE68, [obj("f4d8")])]),
        Vgt(0x717, [obj("f6a0"), emb("f6a8", "suObList")]),
        Vgt(0x72B, [i32("f6f8")]),
        Vgt(0x7D4, [u8("f688")]),
        Vgt(0x7D9, [u8("f968")]),
        Vgt(0x7DD, [emb("f528", "suObList")]),
        Vgt(0x7FA, [Vlt(0xE68, [obj("old_map")])]),
        Vgt(0x7FF, [u32("f9a8")]),
        Vgt(0xA78, [u8("f96c")]),
        Vge(0xBFA, [If(lambda s, ar: ver(ar) <= 0x2399, With200(Flag("has608", [Unmodelled("FUN_4ba0b070 vt 0xa0")], u8)))]),
        Vge(0xC64, With200(Flag("has610", [emb("f610", "moBaseConfiguration_c.f610")], u8))),
        Vge(0xCC2, [obj("f660")]),
        Vgt(0xD7A, [Vlt(0xDAE, [], [emb("fa98", "suObList")]), i32("faf0"), i32("faf4")]),
        Vge(0xDF3, [Vlt(0x23A5, With200([i32("scene_kind"), If(lambda s, ar: s["scene_kind"] in (1, 2), [Unmodelled("swScene_c Serialize")])]))]),
        CondBit(0x200, True),
        Vgt(0xF1D, [i32("n618"), rep(pos("n618"), "f618", [u32("a"), u32("b"), obj("o")])]),
        Vgt(0xF2E, [i32("f784")]),
        Vgt(0xF70, [i32("f788"), f32("f78c"), f32("f790")]),
        Vgt(0xF7C, [
            i32("n358"), rep(pos("n358"), "f358", [obj("o")]),
            i32("n380"), rep(pos("n380"), "f380", [obj("o")]),
        ]),
        Vge(0x12FE, [i32("fb30")]),
        Vge(0x1BE1, [i32("f828"), *[i32(f"f{0x82c + 4 * k:x}") for k in range(6)], i32("f844")]),
        Vgt(0x23E8, [i32("n3d0"), rep(pos("n3d0"), "f3d0", [obj("o")])]),
        Vgt(0x23FC, [i32("f750")]),
        Vge(0x2402, [i32("fbd4")]),
        CondBit(0x200, False),
        Vgt(0x2F72, [i32("f850")]),
        If(lambda s, ar: ver(ar) < 0xCA0 or has_cond(ar, 1), [emb("f4e0", "suObList")]),
        Vgt(0xF9A, [u32("n420"), rep("n420", "f420", [i32("key"), obj("o")])]),
        Vgt(0x1079, [i32("n430"), rep(pos("n430"), "f430", [i32("key"), u32("m"), rep("m", "items", [i32("a"), i32("b")])])]),
        Vgt(0x10F1, int_pairs("nb00", "fb00")),
        Vgt(0x10F7, [i32("fb08")]),
        Vgt(0x1108, [i32("n460"), rep(pos("n460"), "f460", [i32("a"), i32("b")])]),
        Vgt(0x1108, int_pairs("nb10", "fb10")),
        Vgt(0x1193, int_pairs("na50", "fa50", u32)),
        Vgt(0x12DE, [emb("f600", "su_CMapStringToInt")]),
        Vgt(0x142E, [i32("fb34")]),
        Vgt(0x144B, [i32("nb58"), rep(pos("nb58"), "fb58", [i32("key"), emb("v", "moVisualProperties_c.restore")])]),
        Vgt(0x17F7, [emb("fb68", "moCustomPropertyList")]),
        Vgt(0x1BD0, [obj("fb80"), i32("f74c")]),
        Vgt(0x1C2B, [i32("na70"), rep(pos("na70"), "fa70", [i32("v")])]),
        Vgt(0x1FC0, [u32("n450"), rep("n450", "f450", [i32("key"), obj("o")])]),
        Vgt(0x1FF1, With200(Flag("hasb88", [emb("fb88", "mo3DPrintSettings_c.load")]))),
        Vgt(0x1FFB, [u32("nb70"), rep("nb70", "fb70", [cstr("k"), obj("o")])]),
        Vgt(0x23DD, [i32("fbd0")]),
        Vgt(0x2416, int_pairs("nb98", "fb98")),
        Vgt(0x2B7D, [i32("f4c8")]),
        Vgt(0x3721, [i32("f4cc")]),
        Vgt(0x2BDA, [i32("fa80")]),
        Vgt(0x2F53, [obj("fbd8")]),
        If(lambda s, ar: has_cond(ar, 1), [i32("f6f0")]),
        Vgt(0x41A2, [u32("nbf8"), rep("nbf8", "fbf8", [i32("v")])]),
    ])

    reg.define("moBaseConfiguration_c.f610", [
        Vgt(0xE43, [i32("f10")]),
        Vge(0xF1E, [i32("f14")]),
        emb("f08", "suObList"),
    ])

    reg.define("moPartConfiguration_c", [
        base("moBaseConfiguration_c"),
        Vgt(0x87, [Vlt(0x3B3, [Unmodelled("moPartConfiguration_c pre-0x3b3 id list")])]),
        Vgt(0xBC, [emb("f4d0", "moPartConfigObject_c")]),
        Vgt(0xEE, [Vlt(0x1DE, [i32("old_ee")])]),
        Vgt(0x9FE, [f64("fc50"), obj("fc48")]),
        Vgt(0xA56, [i32("fc60")]),
        *With200([Vgt(0xC51, [
            i32("nca8"),
            rep(pos("nca8"), "fca8", [obj("body"), i32("state"), obj("vis")]),
        ])]),
        Vgt(0x12A0, [If(lambda s, ar: not has_cond(ar, 1), [obj("fcb8"), obj("fcc0")])]),
        If(lambda s, ar: ver(ar) == 0x12CC, [i32("n12cc"), rep(pos("n12cc"), "f12cc", [i32("a"), i32("b"), i32("c")])]),
        Vgt(0x12CC, [If(lambda s, ar: not has_cond(ar, 1), [u32("fcc8")])]),
        Vgt(0x141D, [i32("fccc")]),
        Vgt(0x1425, [i32("nce8"), rep(pos("nce8"), "fce8", [i32("a"), i32("b")])]),
        Vgt(0x144D, int_pairs("nd20", "fd20")),
        Vgt(0x1478, [i32("fc64")]),
        Vgt(0x240B, [i32("fcd4")]),
        Vgt(0x2BB1, [i32("fcd0")]),
        Vgt(0x2BDA, [u32("ndc8_hi"), u32("ndc8_lo"), rep(wide("ndc8_hi", "ndc8_lo"), "fdc8", [i32("v")])]),
    ])

    reg.define("moConfigurationMgr_c", [
        CtxSet("ctx3d0", 1),
        Vlt(0x247, [], [base("moFeature_c")]),
        obj("f360"),
        Vlt(0x3B3, [], [obj("f368")]),
        Vgt(0x2D3, [Vlt(0x3B3, [obj("old_arr")])]),
        Vgt(0x3DE, [i32("f40c")]),
        emb("f370", "suObList"),
        Vgt(0x958, [i32("n_ext"), rep(pos("n_ext"), "ext", [obj("o")])]),
        Vgt(0xA65, [Vlt(0xAAC, [Unmodelled("FUN_4c211480 vt 0x28")])]),
        Vgt(0xD90, [i32("f55c")]),
        Vgt(0x1092, [cstr("f578")]),
        Vgt(0x10F1, [i32("n590"), rep(pos("n590"), "f590", [i32("key"), u32("m"), rep("m", "items", [cstr("k"), cstr("v")])])]),
        Vgt(0x11CA, [obj("f5b0")]),
        Vgt(0x11CD, [i32("n5b8"), rep(pos("n5b8"), "f5b8", [i32("a"), u32("b"), u32("c")])]),
        Vgt(0x120F, [u32("n600"), rep("n600", "f600", [i32("key"), obj("o")])]),
        Vgt(0x1295, [Vlt(0x12FE, [obj("f610")])]),
        Vgt(0x12E1, [i32("n5d0"), rep(pos("n5d0"), "f5d0", [i32("key"), i32("m"), rep(pos("m"), "items", [cstr("s")])])]),
        Vgt(0x1416, [i32("f658"), u32("n660"), rep("n660", "f660", [i32("key"), obj("o")])]),
        Vgt(0x17EF, [Vlt(0x17F8, [u32("n670"), rep("n670", "f670", [cstr("k"), cstr("v")])])]),
        Vgt(0x17F7, [Vlt(0x1812, [emb("f698", "moCustomPropertyList")])]),
        Vgt(0x1811, [Vlt(0x182C, [i32("n6a0"), rep(pos("n6a0"), "f6a0", [cstr("k"), u32("m"), rep("m", "items", [cstr("k"), obj("o")])])])]),
        Vgt(0x182B, [u32("n6b0"), rep("n6b0", "f6b0", [cstr("k"), obj("o")])]),
        Vgt(0x1BD4, [obj("f6d0")]),
        Vgt(0x2399, With200([
            i32("n6e0a"), rep(pos("n6e0a"), "f6e0a", [obj("decal"), i32("m")]),
            i32("n6e0b"), rep(pos("n6e0b"), "f6e0b", [i32("key"), i32("m"), rep(pos("m"), "items", [obj("decal")])]),
        ])),
        Vge(0x23A5, With200([
            i32("n6e8a"), rep(pos("n6e8a"), "f6e8a", [obj("scene"), i32("m")]),
            i32("n6e8b"), rep(pos("n6e8b"), "f6e8b", [i32("key"), obj("scene")]),
        ])),
        Vgt(0x23BB, [i32("n708"), rep(pos("n708"), "f708", [obj("o")])]),
        Vgt(0x23C3, [emb("f730", "su_CStringArray")]),
        Vgt(0x27BE, [i32("f758")]),
        Vgt(0x27D5, [u32("f75c")]),
        Vgt(0x3733, [u32("n7f8"), rep("n7f8", "f7f8", [i32("key"), *[emb(f"p{k}", "mgPlane_c.restore") for k in range(3)]])]),
        Vgt(0x3765, [
            cstr("f810"), i32("f818"), i32("f81c"),
            i32("n820"), rep(pos("n820"), "f820", [cstr("k"), cstr("v")]),
            time32("f830"),
        ]),
        Vgt(0x41A2, [i32("n6c0"), rep(pos("n6c0"), "f6c0", [i32("key"), u32("m"), rep("m", "items", [i32("v")])])]),
        Vgt(0x42E8, [i32("f860")]),
        Vgt(0x46C1, Flag("has8a0", [
            u64("n8a0"), rep("n8a0", "f8a0", [i32("key"), i32("a"), i32("b")]),
            u32("n8b0_hi"), u32("n8b0_lo"),
            rep(wide("n8b0_hi", "n8b0_lo"), "f8b0", [
                i32("key"), i32("flag"), u32("m_hi"), u32("m_lo"),
                rep(wide("m_hi", "m_lo"), "items", [i32("v")]),
            ]),
        ])),
        CtxSet("ctx3d0", 0),
    ])

    reg.define("moView_c", [
        cstr("f358"),
        emb("f368", "mgXform_c.restore"),
        emb("f370", "mgXform_c.restore"),
        Vgt(0xEC, [u16("f388"), i32("f38c")]),
        Vge(0x3B0, [f64("f378")]),
        Vgt(0x927, [i32("n380"), rep(pos("n380"), "f380", [obj("o")])]),
        Vgt(0xB79, [i32("f360")]),
        Vge(0x183D, [
            If(ctx_on("ctx3d0"), [CondBit(0x200, True)]),
            *With87c([i32("f394"), *Flag("n398", [emb("f398", "suObList")], i32)]),
            Vgt(0x23EF, With87c([i32("f3a8"), f64("f3b8"), *Flag("n3b0", [emb("f3b0", "suObList")], i32)])),
            If(ctx_on("ctx3d0"), [CondBit(0x200, False)]),
            Vgt(0x23F4, [i32("f3c0")]),
            Vge(0x3764, [i32("f3c8")]),
        ]),
    ])

    reg.define("color", [f64("f08"), f64("f10"), f64("f18")])
    reg.define("pwWallInfo_c", [
        cstr("f08"), cstr("f10"), i32("f18"), i32("f1c"), i32("f20"),
        Vge(0xE11, [i32("f2c")]),
    ])
    reg.define("pwSceneData_c", [
        cstr("f08"), cstr("f10"), cstr("f18"),
        i32("f20"), i32("f24"), i32("f28"), i32("f2c"),
        i32("n30"),
        Vlt(0xDF8,
            [rep(pos("n30"), "f30", [emb("wall", "pwWallInfo_c")])],
            [rep(pos("n30"), "f30", [i32("key"), emb("wall", "pwWallInfo_c")])]),
        f64("f40"), f64("f48"), f64("f50"), f64("f58"),
        i32("f68"), i32("f6c"), i32("f70"), i32("f74"),
        emb("f78", "color"), emb("f98", "color"),
        cstr("fb8"), f64("fc0"), i32("fc8"), i32("fd0"),
        emb("fd8", "color"), emb("ff8", "color"),
        cstr("f118"), f64("f120"), f64("f128"), i32("f130"), i32("f13c"),
        emb("f140", "color"),
        f64("f160"), f64("f168"), i32("f170"), i32("f174"),
        Vgt(0xE0B, [i32("fcc"), i32("f134"), i32("f138")]),
        Vgt(0xF39, [i32("f17c")]),
        Vgt(0x1194, [f64("f198"), f64("f1a0"), f64("f1a8")]),
        Vgt(0x1310, [i32("f180")]),
        Vge(0x17DD, [i32("f1ec")]),
    ])

    reg.define("swWall_c", [
        Vlt(0x117F, [obj("old_pw_material")]),
        i32("f14"),
        Vgt(0xF44, [i32("f18")]),
        Vge(0x117F, [obj("f08"), i32("f10")]),
    ])
    reg.define("swRectWall_c", [
        base("swWall_c"),
        *[f32(f"f{0x20 + 4 * k:02x}") for k in range(12)],
        *[op for k in range(3) for op in (f32(f"f{0x50 + 4 * k:02x}"), f32(f"f{0x5c + 4 * k:02x}"))],
    ])
    reg.define("swCircleWall_c", [
        base("swWall_c"),
        Vgt(0x1827, [f32("f20"), f32("f24"), f32("f28"), f64("f30")]),
        Vge(0x1842, [f64("f38")]),
    ])
    reg.define("swSphereWall_c", [
        base("swWall_c"),
        Vgt(0x1827, [f64("f20"), f64("f28"), f64("f30"), f64("f38")]),
    ])
    walls = {1: "swRectWall_c", 2: "swCircleWall_c", 3: "swSphereWall_c"}
    wall_ops = [
        If(lambda s, ar, k=k: s["kind"] == k, [emb("wall", c)]) for k, c in walls.items()
    ]
    wall_null = If(lambda s, ar: s["kind"] not in walls, [Unmodelled("swScene_c wall kind outside 1..3")])
    reg.define("swScene_c", [
        base("moNode_c"),
        obj("f90"),
        i32("n98"),
        Vlt(0xDF8,
            [rep(pos("n98"), "f98", [i32("kind"), *wall_ops])],
            [rep(pos("n98"), "f98", [i32("key"), i32("kind"), wall_null, *wall_ops])]),
        emb("fa8", "mgBBox_c.restore"),
        i32("f100"),
        emb("f108", "mgXform_c.restore"),
        obj("f190"),
        i32("f198"), f64("f1a0"), i32("f1a8"), f64("f1b0"), f64("f1b8"),
        i32("f1c0"), f32("f1c4"), i32("f1d0"),
        Vgt(0xE51, [i32("f1d8")]),
        Vgt(0xF39, [i32("f1e8")]),
        Vgt(0x1211, [i32("f1f0")]),
        Vgt(0x1827, [i32("f1f4"), f64("f1f8")]),
        Vgt(0x1841, [f64("f200")]),
        Vgt(0x185E, [i32("f208")]),
        Vgt(0x186C, [emb("f210", "mgXform_c.restore")]),
        Vgt(0x42EC, [f64("f2b0"), i32("f2a8")]),
        Vgt(0x46BA, [f64("f2b8")]),
    ])
    for c in ("swCubicalScene_c", "swSphericalScene_c", "swBodyBasedScene_c"):
        concept_vt(c, None)
        reg.define(c, [base("swScene_c")])

    for cls, xml in (("moConfigurationMgr_c", None), ("moPartConfiguration_c", FEATURE_XML)):
        vt(0x4B8, cls, CONCEPT_LW)
        vt(0x4C0, cls, None)
        vt(0x3F8, cls, xml is not None)
        vt(0x3E8, cls, xml)
