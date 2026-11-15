from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, ver, i32, u32, u8, f64, cstr, emb, base
from Schema import If, Rep
from defs.ResolvedCore import xo, obarray, concept_vt, Legacy, PARENT, Vin, has_condition


def flag(name):
    return lambda s, ar: s[name] != 0


def eq(name, value):
    return lambda s, ar: s[name] == value


def signed_count(name):
    return lambda s, ar: max(s[name], 0)


def rev_f818(s, ar):
    return ver(ar) >= 0x186 and not (has_condition(ar, 1) and not ar.ctx.get("ctx874", 0))


def define(reg):
    for c, p in (("moSingleSketchFeature_c", "moSketchedFeature_c"), ("moSketchedFeature_c", "moBodyFeature_c"),
                 ("moExtrusion_c", "moSingleSketchFeature_c"), ("moICE_c", "moExtrusion_c"), ("moCut_c", "moExtrusion_c"),
                 ("moRevolution_c", "moSingleSketchFeature_c"), ("moRevCut_c", "moRevolution_c"),
                 ("moBaseHoleWzd_c", "moSketchedFeature_c"), ("moHoleWzd_c", "moBaseHoleWzd_c"),
                 ("mo3DProfileFeature_c", "moProfileFeature_c")):
        PARENT[c] = p
    for c in ("moCut_c", "moRevolution_c", "moRevCut_c", "moHoleWzd_c", "mo3DProfileFeature_c"):
        concept_vt(c)
    reg.define("mo3DProfileFeature_c", [base("moProfileFeature_c")])
    reg.define("moCut_c", [base("moExtrusion_c")])
    for c in ("moRevolution_c", "moRevCut_c"):
        reg.define(c, [
            base("moBodyFeature_c"),
            xo("f808", "moDisplayDim_c"),
            u8("f824"),
            Vlt(0x15C, [], [xo("f810", "moDisplayDim_c"), i32("f820")]),
            If(rev_f818, [xo("f818", "suObList")]),
            Vgt(0x1CB, [i32("f828")]),
            Vgt(0x7DE, [i32("f870")]),
            Vgt(0x8DE, [xo("f830", "moLineRef_w")]),
            If(lambda s, ar: ver(ar) < 0x10A4 or ver(ar) > 0x10C7,
               [Vgt(0x1173, [xo("f8d8", "moRevEndSpec_c")])],
               [xo("f8d8", "moRevEndSpec_c"), i32("f8e0"), i32("f8e4")]),
            Vgt(0x3F04, [u8("f8e8")]),
        ])
    reg.define("moRevEndSpec_c", [
        i32("f08"),
        i32("f138"),
        i32("f13c"),
        i32("f0c"),
        i32("f10"),
        xo("f118", "moRefWrapper_c"),
        xo("f120", "moRefWrapper_c"),
        xo("f128", "moPointRef_w"),
        xo("f130", "moPointRef_w"),
        f64("f38"),
        f64("f40"),
        i32("f140"),
        i32("f144"),
        Vlt(0x11C3, [f64("f150"), f64("f158")], [
            xo("f18", "moDisplayDim_c"),
            xo("f20", "moDisplayDim_c"),
            Vgt(0x11E1, [xo("f28", "moDisplayDim_c"), xo("f30", "moDisplayDim_c")]),
        ]),
    ])
    reg.define("moSlotCenterAxisData_c", [
        emb("f08", "mgPoint_c.restore"),
        emb("f20", "mgPoint_c.restore"),
        f64("f38"),
        f64("f40"),
        f64("f48"),
    ])
    reg.define("moHoleWzd_c", [
        base("moBodyFeature_c"),
        Vin(0x2F46, 0x2F68, [i32("old_2f46")]),
        i32("f814"),
        xo("f818"),
        f64("f820"),
        Vge(0x2EF, [i32("f828")]),
        Vge(0x2FA, [cstr("f830"), cstr("f838")]),
        Vgt(0x4FF, [
            i32("f84c"), i32("f850"), i32("f854"),
            cstr("f858"), cstr("f860"), cstr("f868"),
            f64("f878"), f64("f880"), f64("f888"), f64("f890"), f64("f898"),
        ]),
        Vgt(0x50F, [cstr("f870")]),
        Vgt(0x659, [i32("f8a0")]),
        Vgt(0x721, [i32("f8d0")]),
        Vgt(0x779, [cstr("f8a8")]),
        Vgt(0x834, [cstr("f8b8")]),
        Vgt(0x838, [i32("f918"), i32("f91c")]),
        Vgt(0x847, [cstr("f8c0")]),
        Vge(0xAD5, [i32("f848")]),
        Vgt(0xADD, [i32("n960"), Rep(signed_count("n960"), "f960", [i32("k"), f64("v")])]),
        Vgt(0xB5F, [
            i32("f8d4"), i32("f8d8"), i32("f8dc"), i32("f8e0"), i32("f8e4"), i32("f8e8"), i32("f8f0"), i32("f8f4"),
            f64("f8f8"),
        ]),
        Vgt(0xB64, [i32("f900"), i32("f904"), i32("f8ec"), cstr("f8c8")]),
        Vgt(0xCDF, [i32("f988")]),
        Vge(0xCF2, [i32("f908"), i32("f90c")]),
        Vgt(0xE59, [i32("f910"), i32("f914"), i32("f920")]),
        Vgt(0x140B, [i32("fa34"), i32("fa30"), cstr("fa38"), cstr("fa40")]),
        Vgt(0x17DB, [i32("fa48"), f64("fa50"), i32("fa60"), i32("fa64"), i32("fa68")]),
        Vgt(0x2F47, [i32("f9a0")]),
        Vgt(0x332E, [i32("fbb8")]),
        If(lambda s, ar: s.get("fa48", 0) != 0, [
            Vgt(0x17ED, [
                xo("fa70", "moDisplayDistanceDim_c"),
                Vlt(0x2B5E, [Rep(signed_count("n960"), "fbe0", [emb("slot", "moSlotCenterAxisData_c")])], [
                    i32("nbe0"),
                    Rep(signed_count("nbe0"), "fbe0", [emb("slot", "moSlotCenterAxisData_c")]),
                ]),
            ]),
        ]),
        If(lambda s, ar: s.get("fa48", 0) != 0, [
            Vgt(0x17F8, [i32("fa78"), i32("fa7c"), i32("fa80"), xo("fa88", "moDisplayDim_c")]),
        ]),
        If(lambda s, ar: s.get("fa48", 0) != 0, [
            Vgt(0x1856, [Vlt(0x42EA, [i32("f844")]), f64("fab0"), f64("fab8"), f64("fac0")]),
        ]),
        Vgt(0x3355, [f64("fbb0")]),
        Vgt(0x3F02, [u8("fc00"), i32("fc04"), i32("fc08"), obarray("fc10")]),
        Vgt(0x42E9, [i32("f844")]),
    ])
    reg.define("moContact_c.FUN_4cb6aa00", [
        obarray("f50"),
        Vge(0xA6B, [f64("f90")]),
        Vge(0xAE9, [i32("f98"), xo("fa0", "moDisplayAngularDim_c")]),
        Vge(0xB42, [f64("fa8"), i32("fb0"), i32("fb8")]),
        Vge(0xCAA, [i32("fc8")]),
        Vge(0xC72, [i32("fcc")]),
        Vge(0xC92, [xo("fe0", "moLoftSynchRef_c")]),
        Vgt(0xCFF, [u32("f40"), u32("f44"), u32("f48")]),
        Vge(0xD8A, [f64("fc0")]),
    ])
    reg.define("moLoftSynchRef_c", [
        base("moEndPointRef_w"),
        i32("f100"),
        u32("f104"),
        u32("f108"),
        Vgt(0xA1E, [f64("f110")]),
        Vgt(0xBA8, [xo("f1a8", "moRefWrapper_c")]),
        Vgt(0xC71, [i32("f1a4"), i32("f1b0"), xo("f1b8", "moPointRef_w"), f64("f1c0")]),
        Vgt(0xC79, [f64("f1c8")]),
        Vge(0x11B7, [f64("f118"), f64("f120"), emb("f128", "mgPoint_c.restore"), emb("f140", "mgPoint_c.restore")]),
        Vge(0x1213, [xo("f1d0", "moCurveRef_w"), xo("f1d8", "moCurveRef_w")]),
    ])
    reg.define("moWireContact_c", [
        base("moContact_c.FUN_4cb6aa00"),
        xo("fe8", "moRefWrapper_c"),
    ])
    reg.define("moPerBodyChooserDataWithFileName_c", [
        base("moPerBodyChooserData_c"),
        cstr("f98"),
        Vgt(0x777, [xo("fa0", "moRefWrapper_c")]),
        Vge(0x77C, [i32("fa8")]),
    ])
    for c in ("moExtrusion_c", "moICE_c"):
        concept_vt(c)
        reg.define(c, [
            base("moBodyFeature_c"),
            xo("f818", "moEndSpec_c"),
            Vgt(0x997, [f64("f838")]),
            If(lambda s, ar: ver(ar) > 0xDBE, [i32("f810")]),
        ])
    reg.define("moEndSpec_c", [
        Vgt(0x8E2, [xo("f138", "moDirectionSpec_c")]),
        i32("f08"),
        i32("f88"),
        i32("f8c"),
        Vge(0x1D4, [
            Vlt(0x1DD, [Legacy("moEndSpec_c f90 0x1d4-0x1dc")], [xo("f90")]),
        ]),
        i32("f0c"),
        i32("f10"),
        xo("f18", "moDisplayDim_c"),
        xo("f20", "moDisplayDim_c"),
        Vlt(0x301, [Legacy("moEndSpec_c surface refs pre-0x301")], [
            If(eq("f0c", 3), [xo("f68")]),
            u8("has_f28"),
            If(flag("has_f28"), [obarray("f28")]),
            If(eq("f10", 3), [xo("f70")]),
            u8("has_f48"),
            If(flag("has_f48"), [obarray("f48")]),
        ]),
        f64("fa0"),
        i32("fb8"),
        i32("fbc"),
        i32("fc0"),
        i32("fc4"),
        Vgt(0x748, [i32("fb0"), i32("fb4")]),
        xo("fc8", "moDisplayDim_c"),
        xo("fd0", "moDisplayDim_c"),
        Vgt(0xD1, [i32("fa8"), i32("fac")]),
        Vgt(0x131, [i32("fd8"), i32("fdc")]),
        Vgt(0x3FD, [obarray("fe0")]),
        Vgt(0x3FE, [obarray("f100")]),
        Vgt(0x645, [i32("f128")]),
        Vge(0x688, [i32("f12c")]),
        Vge(0x23F7, [i32("f130")]),
        Vge(0x86A, [
            If(eq("f0c", 7), [xo("f78")]),
            If(eq("f10", 7), [xo("f80")]),
        ]),
        Vgt(0xA58, [xo("f140", "moFromEndSpec_c")]),
        Vge(0x116C, [i32("f148"), i32("f14c"), i32("f150"), i32("f154")]),
        Vge(0x3B01, [i32("f158")]),
    ])
    reg.define("moFromEndSpec_c", [
        i32("t"),
        If(lambda s, ar: s["t"] in (1, 2), [xo("f08", "moRefWrapper_c")]),
        If(eq("t", 5), [xo("f28", "moDisplayDim_c"), i32("f20")]),
        If(eq("t", 4), [f64("f18"), i32("f20")]),
        If(eq("t", 3), [
            Vgt(0x1065, [xo("f28", "moDisplayDim_c")], [f64("f18")]),
            i32("f20"),
        ]),
    ])
    reg.define("moFR_c", [
        xo("f08", "moExtObject_c"),
        Vlt(0x2CB, [Legacy("moFR_c pre-0x2cb")], [emb("f10", "moFRData_c")]),
    ])
    reg.define("moFavoriteHandle_c", [
        i32("f08"),
        i32("f0c"),
        Vgt(0x72C, [u32("f10")]),
    ])
    reg.define("moPerBodyChooserData_c", [
        obarray("f08"),
        obarray("f28"),
        Vgt(0x518, [obarray("f48")]),
        Vgt(0x754, [i32("f68"), i32("f6c")]),
        Vgt(0x84E, [emb("f78", "su_CDWordArray")]),
        Vgt(0x995, [i32("f70")]),
    ])
    reg.define("moBBoxCenterData_c", [
        i32("f08"),
        emb("f10", "mgPoint_c.restore"),
        Vgt(0xFC6, [f64("f28")]),
    ])
