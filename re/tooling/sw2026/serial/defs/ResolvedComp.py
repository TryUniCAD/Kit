from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, i32, u32, u8, cstr, emb, base, time32
from Schema import If, Rep
from defs.ResolvedCore import xo, node_vt, vt, Cnd, Legacy, has_condition


def comp_needs_fr(s, ar):
    if s.get("cond_fr", 0) != 0:
        return True
    if not has_condition(ar, 1):
        return True
    if has_condition(ar, 0x200000):
        return True
    return bool(ar.ctx.get("ctx874", 0) or ar.ctx.get("ctx894", 0))


def define(reg):
    node_vt("moHistoryFeatItemData_c")
    for c in ("moCompFeature_c", "moCompRefPlane_c", "moCompSolidBody_c", "moCompProfile_c", "moCompRefAxis_c"):
        vt(0x4B8, c, None)
        vt(0x4C0, c, None)
    reg.define("moHistoryFeatItemData_c", [
        Vge(0x17E6, [base("moNode_c")]),
        Vgt(0x17E5, [xo("f48", "moCompFeature_c")]),
    ])
    reg.provisional("moComponent_c", [
        Vgt(100, [Vlt(0x144, [Legacy("moComponent_c name pre-0x144")])]),
        xo("owner"),
        Vgt(0x846, [Vlt(0x84B, [Legacy("moComponent_c obarray 0x847-0x84a")])]),
    ])
    reg.provisional("moUnitComponent_c", [
        base("moComponent_c"),
        Cnd(1, [Cnd(0x6200, [], [Legacy("moUnitComponent_c condition 1")])]),
        u8("has_ext"),
        If(lambda s, ar: s["has_ext"] != 0, [
            If(lambda s, ar: ar.ctx.get("has_owner", 1), [xo("ext", "moExtObject_c")]),
        ], [
            Vlt(0x3B3, [Legacy("moUnitComponent_c model pre-0x3b3")]),
        ]),
    ])
    reg.define("moFRData_c", [
        i32("f00"),
        Vlt(0x4A5, [cstr("old_name")]),
        time32("f08"),
        Vlt(0xD7B, [u32("old_d7b")]),
        Vlt(0xC77, [Vgt(0xA63, [i32("old_a63")])]),
    ])
    reg.define("moCompRef_c", [
        xo("f58", "moComponent_c"),
        Vgt(0x42, [Vlt(0x4B, [Legacy("moCompRef_c external name pre-0x4b")])]),
        Vgt(0xE9, [i32("f68")]),
        Vgt(0x494, [i32("f18")]),
        Vgt(0x752, [i32("f1c")]),
        Vgt(0xDA5, [i32("f20"), i32("f30")]),
        Vlt(0x756, [], [i32("f70")]),
        Vgt(0xD9A, [
            i32("f84"),
            If(lambda s, ar: s["f84"] != 0, [emb("f88", "moOldRef_c")]),
        ]),
        Vgt(0xDB0, [i32("fa0")]),
        Vgt(0xFB6, [u32("f34")]),
        Vgt(0x11AB, [i32("f48")]),
        Vgt(0x279F, [Vlt(0x27A8, [i32("f94")])]),
        Vgt(0x27A7, [i32("f90"), i32("f94"), i32("f98"), i32("f9c")]),
        Vgt(0x27B1, [
            i32("has_fb0"),
            If(lambda s, ar: s["has_fb0"] != 0, [xo("fb0", "moFacetedData_c")]),
        ]),
        Vgt(0x27CA, [Vlt(0x27CC, [cstr("fb8_old")])]),
        Vgt(0x27CB, [
            i32("has_fb8"),
            If(lambda s, ar: s["has_fb8"] != 0, [cstr("fb8")]),
        ]),
        Vgt(0x2B60, [
            i32("has_fc0"),
            If(lambda s, ar: s["has_fc0"] != 0, [emb("fc0", "moCompRefInfo_c")]),
        ]),
        Vgt(0x2BB8, [
            i32("has_fc8"),
            If(lambda s, ar: s["has_fc8"] != 0, [emb("fc8", "mgXform_c.restore")]),
        ]),
        Vgt(0x2F55, [
            i32("has_fd0"),
            If(lambda s, ar: s["has_fd0"] != 0, [cstr("fd0")]),
        ]),
        Vge(0x3EF6, [u32("f4c")]),
    ])
    reg.define("moCompFeature_c", [
        base("moCompRef_c"),
        Vlt(0x2C9, [Legacy("FUN_4bbacf80 pre-0x2c9")], [
            Cnd(1, [Cnd(0x10000, [i32("cond_fr")])]),
            If(comp_needs_fr, [emb("ff0", "moFRData_c")], [
                i32("has_ff0"),
                If(lambda s, ar: s["has_ff0"] != 0, [emb("ff0", "moFRData_c")]),
            ]),
        ]),
    ])
    reg.define("moCompRefPlane_c", [
        Vlt(0x2D1, [Legacy("FUN_4bbab230 pre-0x2d1")], [
            base("moCompFeature_c"),
            xo("ff8", "moRefGeom_c"),
        ]),
        Vgt(0x4BB, [i32("f100")]),
    ])
    reg.define("moCompProfile_c", [base("moCompFeature_c")])
    reg.define("moCompEntGroup_c", [
        base("moCompRef_c"),
        i32("fe8"),
        emb("ff0", "rf.suObList"),
        emb("f138", "rf.suObList"),
    ])
    reg.provisional("moContextUnitComponent_c", [
        base("moComponent_c"),
        xo("f28", "moExtObject_c"),
        Vge(0x38D, [i32("f30")]),
        Vge(0x8FD, [emb("f38", "moReferencedConfiguration_c")]),
    ])
    reg.define("moCompRefAxis_c", [
        Vlt(0x2D1, [Legacy("FUN_4bbab230 pre-0x2d1")], [
            base("moCompFeature_c"),
            xo("ff8", "moRefGeom_c"),
        ]),
    ])
    reg.define("moCompSolidBody_c", [
        base("moCompRef_c"),
        Vgt(0x49A, [xo("ff0", "moFaceRef_c")]),
        Vgt(0x864, [
            i32("n110"),
            Rep(lambda s, ar: max(s["n110"], 0), "f110", [i32("v")]),
        ]),
        Vgt(0x94D, [i32("f108")]),
        Vge(0x1040, [i32("f104"), i32("f100")]),
    ])
