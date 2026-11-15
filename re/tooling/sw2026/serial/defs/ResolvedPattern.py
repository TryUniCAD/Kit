from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, ver, i32, u32, u8, f64, cstr, emb, base, count
from Schema import If, Rep
from defs.ResolvedCore import xo, obarray, concept_vt, Legacy, PARENT, OIf, VT, vt, has_condition, Vin

DIM_INC = "moDimIncrementId_c.Serialize"
ORIG_DIM = "moOrigDimData_c.Serialize"
SHAPE = "moShapePatternData_c.FUN_4bb1ed50"
PATTERN = "moPattern_c.FUN_4bb1aa00"


def flag(name):
    return lambda s, ar: s[name] != 0


def signed_count(name):
    return lambda s, ar: max(s[name], 0)


def slot(n):
    return lambda o: bool(VT.get(n, {}).get(o.cls))


def nonnull(*names):
    return lambda s, ar: any(s.get(n) is not None for n in names)


def define(reg):
    for c in ("moMirrorPattern_c", "moCirPattern_c", "moLPattern_c"):
        concept_vt(c)
        PARENT[c] = "moPattern_c"
        vt(0x870, c, False)
        vt(0x2678, c, False)
    PARENT["moPattern_c"] = "moBodyFeature_c"
    reg.provisional("suObArray", [base("rf.suObArray")])
    reg.define("rf.su_CMapObToInt", [count("n"), Rep("n", "items", [xo("k"), i32("v")])])
    reg.define(DIM_INC, [
        u8("f00"),
        xo("f08", "moDimHandle_c"),
        u8("has_f10"),
        If(flag("has_f10"), [cstr("f10")]),
        i32("f18"),
        i32("f1c"),
        Vgt(0x1C0B, [i32("f20")]),
        u8("f40"),
        xo("f48", "moDisplayDim_c"),
        Vgt(0x1C32, [u8("f24"), f64("f28")]),
        Vgt(0x1C54, [i32("f50")]),
        Vge(0x1FE5, [u8("f30"), f64("f38")]),
    ])
    reg.define(ORIG_DIM, [
        u8("f00"),
        xo("f08", "moDimHandle_c"),
        u8("has_f10"),
        If(flag("has_f10"), [cstr("f10")]),
        u8("f18"),
        f64("f20"),
        u8("fb4"),
        f64("fb8"),
        f64("fc0"),
        Vgt(0x1C54, [i32("f260")]),
        Vgt(0x1C0B, [i32("fc8"), i32("fcc"), i32("fd0"), i32("fd4"), i32("f1d8")]),
        i32("f1d0"),
        i32("f1d4"),
        i32("f218"),
        u8("has_f228"),
        If(flag("has_f228"), [emb("f228", DIM_INC)]),
        i32("n1e0"),
        Rep(signed_count("n1e0"), "f1e0", [xo("feat", "moCompFeature_c")]),
        i32("f1c0"),
        obarray("f1b0"),
        Vge(0x1C34, [i32("f25c")]),
    ])
    reg.define(SHAPE, [
        i32("f30"),
        If(flag("f30"), [
            Vlt(0xBEE, [f64("f38")], [
                If(lambda s, ar: s["f30"] == 1, [xo("f48", "moDisplayRadialDim_c")]),
                If(lambda s, ar: s["f30"] == 2, [xo("f50", "moDisplayDistanceDim_c")]),
                If(lambda s, ar: s["f30"] == 3, [xo("f58", "moDisplayDistanceDim_c"), xo("f50", "moDisplayDistanceDim_c")]),
                If(lambda s, ar: s["f30"] == 4, [xo("f40", "moDisplayRadialDim_c"), xo("f48", "moDisplayRadialDim_c")]),
            ]),
            Vlt(0xBD0, [xo("f68", "moRefWrapper_c")], [
                i32("f98"),
                If(flag("f98"), [emb("f90", "mgPoint_c.restore")], [xo("f68", "moRefWrapper_c")]),
            ]),
            Vlt(0xBD5, [xo("f70", "moRefWrapper_c")], [emb("f18", "mgVector_c.restore")]),
            If(lambda s, ar: s["f30"] != 1, [
                Vlt(0xBCE, [Legacy("moShapePatternData_c old reference pre-0xbce")]),
                If(lambda s, ar: (s["f30"] - 2) & 0xFFFFFFFF > 1, [i32("f80")]),
                Vgt(0xBCD, [Vlt(0xBEE, [f64("f88")], [xo("f60", "moDisplayAngularDim_c")])]),
            ]),
            Vge(0xBEB, [i32("f9c")]),
        ]),
    ])
    reg.define("moMatrixIndexHelper_c", [obarray("f10"), obarray("f30"), i32("f08")])
    reg.define(PATTERN, [
        base("moBodyFeature_c"),
        Vlt(0x80, [Legacy("moPattern_c seed pre-0x80")]),
        If(lambda s, ar: has_condition(ar, 0x2000) and ver(ar) > 0x10BA,
           [Legacy("moPattern_c FR seed list under condition 0x2000")],
           [xo("f988", "suObList")]),
        Vgt(0x73E, [xo("f9d8", "suObList")]),
        Vlt(0xEB, [], [i32("f9e0")]),
        Vlt(0x1C1, [], [xo("f820", "suObArray")]),
        Vgt(0x2DF, [u8("f9fc")]),
        Vgt(0x3DF, [i32("fa00")]),
        Vlt(0x7F7, [], [
            xo("f8d8", "suObList"),
            Vlt(0x42CF, [u8("f948")], [xo("f8e0", "suObList"), i32("f948")]),
            xo("f950", "moMatrixIndexHelper_c"),
        ]),
        Vgt(0x82C, [
            emb("f840", "rf.su_CMapObToInt"),
            count("n870"),
            Rep("n870", "f870", [xo("k"), xo("v")]),
        ]),
        Vge(0x9A0, [u8("f9f0")]),
        Vgt(0xA55, [obarray("ff50")]),
        Vgt(0xB54, [emb("ffa0", SHAPE)]),
        Vgt(0xB71, [u8("f1050")]),
        Vgt(0xBA7, [u8("f1054")]),
        Vgt(0x1437, [
            Vin(0x1C0C, 0x1C29, [Legacy("moPattern_c dimension pattern data 0x1c0c-0x1c28")]),
            i32("nf30"),
            Rep(signed_count("nf30"), "ff30", [emb("inc", DIM_INC)]),
            u8("fa04"),
            u8("fa08"),
            OIf(slot(0x870), [
                Vgt(0x1C0B, [i32("nf90"), Rep(signed_count("nf90"), "ff90", [i32("v")])]),
            ]),
            i32("na10"),
            Rep(signed_count("na10"), "fa10", [emb("dim", ORIG_DIM)]),
            i32("na30"),
            Rep(signed_count("na30"), "fa30", [emb("dim", ORIG_DIM)]),
            emb("fa50", ORIG_DIM),
            emb("fcb8", ORIG_DIM),
        ]),
        Vgt(0x1FB6, [xo("f990", "suObList")]),
        Vgt(0x1FDC, [i32("f1128")]),
        Vgt(0x2F86, [emb("f8e8", "rf.suObList")]),
        Vgt(0x2F93, [u32("n930"), Rep("n930", "f930", [i32("v")])]),
        Vgt(0x3745, [u8("f112c")]),
        Vge(0x42DC, [u8("f1130")]),
    ])
    reg.define("moMirrorPattern_c", [
        base(PATTERN),
        Vgt(0x3745, [xo("f11b0", "moPlaneRef_w")]),
        emb("f1140", "moPlaneRef_w"),
    ])
    reg.define("moCirPattern_c", [
        base(PATTERN),
        xo("f1138", "moDisplayDim_c"),
        xo("f1140", "moDisplayDim_c"),
        Vgt(0x239B, [xo("f1148", "moDisplayDim_c"), xo("f1150", "moDisplayDim_c")]),
        If(lambda s, ar: has_condition(ar, 0x800), [i32("owner_id")]),
        xo("f1158", "moDimHandle_c"),
        Vlt(0x90, [Legacy("moCirPattern_c axis edge pre-0x90")], [xo("f1160", "moLineRef_w"), u8("f1168")]),
        Vgt(0x3FB, [
            xo("f11a0", "moDisplayAngularDim_c"),
            u8("f11b0"),
            Vgt(0x239B, [
                xo("f11a8", "moDisplayAngularDim_c"),
                u8("f11b4"), u8("f11b8"), u8("f11bc"), u8("f11c8"), u8("f11cc"),
            ]),
        ]),
        If(nonnull("f1140", "f11a0"), [
            Vgt(0x103A, [
                i32("n11d8"),
                Rep(signed_count("n11d8"), "f11d8", [
                    i32("k"),
                    i32("m"),
                    Rep(signed_count("m"), "ids", [i32("v")]),
                ]),
                i32("n1208"),
                Rep(signed_count("n1208"), "f1208", [i32("v")]),
            ]),
            Vgt(0x3EFA, [emb("f1170", "mgPoint_c.restore"), emb("f1188", "mgVector_c.restore")]),
        ], [Legacy("moCirPattern_c without angular dimension throws")]),
    ])
    reg.define("moLPattern_c", [
        base(PATTERN),
        OIf(slot(0x2678), [
            Vlt(0xBE3, [Legacy("moLPattern_c dims pre-0xbe3 with vt 0x2678")]),
        ], [
            xo("f1258", "moDisplayDim_c"),
            xo("f1260", "moDisplayDim_c"),
            xo("f1268", "moDisplayDim_c"),
            xo("f1270", "moDisplayDim_c"),
        ]),
        u8("f1298"),
        u8("f129c"),
        xo("f1278"),
        xo("f1280"),
        Vlt(0x1C9, [Legacy("moLPattern_c direction edges pre-0x1c9")], [
            xo("f1288", "moLineRef_w"),
            xo("f1290", "moLineRef_w"),
        ]),
        Vgt(0x694, [u8("f12a4")]),
        Vgt(0x1BFE, [
            i32("f12e0"), i32("f12e4"),
            xo("f12e8", "moRefWrapper_c"), xo("f12f0", "moRefWrapper_c"),
            i32("f12f8"), i32("f12fc"),
            xo("f1300", "moRefWrapper_c"), xo("f1308", "moRefWrapper_c"),
            i32("f1310"), i32("f1314"),
            xo("f1318", "moDisplayDim_c"), xo("f1320", "moDisplayDim_c"),
        ]),
        Vgt(0x1C01, [i32("f1328"), i32("f132c")]),
        Vge(0x3F00, [u8("f12a0")]),
    ])
