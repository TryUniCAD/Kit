from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, ver, i32, u32, u16, u8, f64, cstr, emb, base
from Schema import If, Rep
from defs.ResolvedCore import xo, obarray, concept_vt, Cnd, Legacy, Kind, PARENT, has_condition, Vin, FEATURE_XML


def flag(name):
    return lambda s, ar: s[name] != 0


def signed_count(name):
    return lambda s, ar: max(s[name], 0)


def serialize_ptr(name):
    return [i32(f"has_{name}"), If(flag(f"has_{name}"), [obarray(name)])]


def chooser(name):
    return [u16(f"has_{name}"), If(flag(f"has_{name}"), [emb(name, "moBodyChooser_c")])]


def atom_bvar11(s, ar):
    return has_condition(ar, 0x2000) and ver(ar) >= 0x10BB


def atom_bvar10(s, ar):
    return not has_condition(ar, 1)


def define(reg):
    for c, p in (("moAtomFeature_c", "moModelFeature_c"), ("moBodyFeature_c", "moAtomFeature_c"),
                 ("moRefGeom_c", "moAtomFeature_c"), ("moRefPlane_c", "moRefGeom_c"),
                 ("moDefaultRefPlnData_c", "moAbsoluteRefPlnData_c")):
        PARENT[c] = p
    concept_vt("moRefPlane_c", "moRefPlane_c.SerializeXmlData")
    reg.provisional("mgPoint_c.restore", [f64("x"), f64("y"), f64("z")])
    reg.provisional("mgVector_c.restore", [f64("x"), f64("y"), f64("z")])
    reg.provisional("mgMatrix_c.restore", [f64(f"m{k}") for k in range(9)])
    reg.provisional("mgPerspInfoBase_c.restore", [f64(f"p{k}") for k in range(4)])
    reg.provisional("mgPerspInfo_c.restore", [f64(f"p{k}") for k in range(6)])
    reg.provisional("mgMatrix5_c.restore", [i32("dim")] + [f64(f"m{k}") for k in range(25)])
    reg.provisional("mgXform_c.restore", [
        u8("has_matrix"),
        If(flag("has_matrix"), [emb("matrix", "mgMatrix_c.restore")]),
        f64("t0"), f64("t1"), f64("t2"), f64("scale"),
        u8("flags"),
        If(lambda s, ar: s["flags"] & 0xF0 == 0x10, [emb("persp", "mgPerspInfoBase_c.restore")]),
        If(lambda s, ar: s["flags"] & 0xF0 == 0x20, [emb("persp", "mgPerspInfo_c.restore")]),
        If(lambda s, ar: s["flags"] & 0xF0 == 0x40, [emb("persp", "mgMatrix5_c.restore")]),
    ])
    reg.define("moIdKeeper_c", [])
    reg.define("moPMarkRecord_c", [i32("f18")])
    reg.define("moBodyChooser_c", [
        obarray("f48"),
        Vgt(0x4A6, [xo("f68", "moAtomFeature_c")]),
    ])
    reg.define("moAtomFeature_c.f6a8", [
        i32("n"),
        Rep(signed_count("n"), "items", [
            u32("key"),
            i32("val"),
            If(lambda s, ar: s["val"] < 0, [
                Vgt(0x1059, [
                    i32("has_set"),
                    If(flag("has_set"), [
                        i32("m"),
                        Rep(signed_count("m"), "set", [i32("v")]),
                    ]),
                ]),
            ]),
        ]),
    ])
    reg.define("moAtomFeature_c", [
        base("moModelFeature_c"),
        Vgt(0x392, [
            obarray("f368"),
            obarray("f388"),
            u16("has_f3a8"),
            If(flag("has_f3a8"), [xo("f3a8", "moIdKeeper_c")]),
        ]),
        Vgt(0x487, [
            If(atom_bvar10, [
                *serialize_ptr("f528"),
                *serialize_ptr("f530"),
                xo("f538", "moAtom_c"),
            ]),
        ]),
        Vgt(0x490, [
            Cnd(1, [], [
                If(atom_bvar11, [], [
                    i32("n494"),
                    Rep(signed_count("n494"), "f498", [i32("v")]),
                ]),
            ]),
            Vgt(0x491, [i32("f540")]),
        ]),
        Vgt(0x823, [*serialize_ptr("f548"), i32("f544")]),
        Vgt(0x82F, chooser("f4a8")),
        Vgt(0x83B, [u16("f4a0")]),
        Vgt(0x842, chooser("f4b0")),
        Vgt(0x10F8, [i32("f4b8"), *chooser("f4c0"), *chooser("f4c8")]),
        Vgt(0x85F, [i32("f578")]),
        Vgt(0x874, serialize_ptr("f550")),
        If(lambda s, ar: has_condition(ar, 0) or has_condition(ar, 0x400000), [
            Vgt(0x8DD, [
                i32("has_f3d0"),
                If(flag("has_f3d0"), [
                    xo("f3d0", "moPMarkRecord_c"),
                    i32("f3c0"),
                    i32("f3c8"),
                    i32("f580"),
                ]),
            ]),
        ]),
        Vge(0x8F3, [i32("f5d0")]),
        Vgt(0x91A, [
            i32("n678"),
            Rep(signed_count("n678"), "f678", [i32("k"), i32("v")]),
        ]),
        Vgt(0xA5D, [
            i32("n5d8"),
            Rep(signed_count("n5d8"), "f5d8", [xo("k", "moCompEdge_c"), u32("v")]),
        ]),
        Vgt(0xA5F, [
            i32("n400"),
            Rep(signed_count("n400"), "f400", [i32("k"), i32("v")]),
        ]),
        Vgt(0xCE4, [i32("f490")]),
        Vgt(0x1037, [
            u32("n3e0"),
            Rep("n3e0", "f3e0", [i32("k"), xo("v", "moVisualProperties_c")]),
        ]),
        Vgt(0x104C, [
            i32("has_f6a8"),
            If(flag("has_f6a8"), [emb("f6a8", "moAtomFeature_c.f6a8")]),
        ]),
        Vgt(0x1100, [
            i32("n610"),
            Rep(signed_count("n610"), "f610", [xo("face", "moCompFace_c"), cstr("name")]),
            i32("n620"),
            Rep(signed_count("n620"), "f620", [i32("k"), cstr("name")]),
        ]),
        Vgt(0x17E3, [i32("f6bc")]),
    ])
    reg.define("moBodyFeature_c", [
        base("moAtomFeature_c"),
        Vin(0x6B, 0x3AA, [f64("old_f1e0")]),
        Vgt(0x6E, [xo("f6e0", "moAsmFeatData_c")]),
        Vgt(0xF4C, [Cnd(1, [], [xo("f758", "moCompFeature_c")])]),
        Vgt(0x10A3, [obarray("f780")]),
        Vgt(0x11E7, [i32("f7a0")]),
    ])
    reg.define("moRefGeom_c", [
        base("moAtomFeature_c"),
        emb("f6c0", "mgPoint_c.restore"),
        i32("f6dc"),
        Vgt(0x3E2, [i32("f6e0")]),
        Vgt(0x145C, [xo("f6e8", "moFeatureRefWrapper_c")]),
        Vgt(0x2F85, [i32("f6f0")]),
    ])
    reg.define("moRefPlane_c", [
        base("moRefGeom_c"),
        xo("f6f8", "moRefPlnData_c"),
    ])
    reg.define("moRefPlane_c.SerializeXmlData", [
        If(lambda s, ar: s["f08"] != -1, [base(FEATURE_XML)]),
    ])
    reg.define("moRefPlnData_c.serializePlaneData", [
        emb("root", "mgPoint_c.restore"),
        emb("normal", "mgVector_c.restore"),
        emb("f20", "mgXform_c.restore"),
        Vlt(0x160, [Legacy("moRefPlnData_c border pre-0x160")], [
            f64("b0"), f64("b1"), f64("b2"), f64("b3"),
        ]),
        xo("f48", "moCompEdge_c"),
        i32("f50"),
        i32("f54"),
        i32("f58"),
        If(lambda s, ar: 0xD9 < ver(ar) < 0xE6, [Legacy("moRefPlnData_c 0xda-0xe5")], [
            Vgt(0xE5, [u8("old_e5")]),
        ]),
        Kind("moDefaultRefPlnData_c", [Vgt(0x81D, [emb("display_root", "mgPoint_c.restore")])]),
        Vgt(0xE24, [i32("f5c")]),
        Vgt(0x10DA, [i32("f60")]),
        Vgt(0x17DD, [u16("f64")]),
        Vgt(0x2B83, [xo("f68", "moCompFaceMeshFacetFin_c")]),
        Vgt(0x2BA5, [xo("f70", "moRefAxis_c"), xo("f78", "moCompSketchEntHandle_c")]),
    ])
    for c in ("moRefPlnData_c", "moDefaultRefPlnData_c"):
        reg.define(c, [base("moRefPlnData_c.serializePlaneData")])
