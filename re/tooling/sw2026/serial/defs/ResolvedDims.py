from __future__ import annotations

from Core import ArchiveError
from Dsl import Vgt, Vge, Vlt, ver, i32, u32, u16, i16, u8, i64, f32, f64, cstr, emb, base
from Schema import Op, If, Rep, Raw, run_load, run_store
from defs.ResolvedCore import xo, obarray, Cnd, Legacy, Vin, PARENT, isa, has_condition, node_vt, vt, VT

DIMENSION = "Dimension_c.Serialize"
FEATURE_DIM = "moFeatureDim_c.FUN_4c833f00"
REF_DIM = "moRefDim_c.FUN_4c836660"
DIM_HANDLE = "moDimHandle_c.FUN_4c82a810"
MOD_HANDLE = "moModDimHandle_c.Serialize"
SK_HANDLE = "moSkDimHandle_c.Serialize"
DISPLAY_OBJECT = "moDisplayObject_c.FUN_4ba4d3c0"
DISPLAY_ITEM = "moDisplayItem_c.Serialize"
DISPLAY_DIM = "moDisplayDim_c.FUN_4c82c3d0"
RADIAL = "moDisplayRadialDim_c.FUN_4c8320a0"
ARC = "moDisplayArcDim_c.FUN_4c82b8f0"
PARAM = "dm.moParameter_c.FUN_4c17a330"
DOUBLE_PARAM = "dm.moDoubleParameter_c.FUN_4c177fe0"
EXT_SKETCH = "moSketchToolsUserObject_c.FUN_4c5ba000"
DYNARRAY = "dm.FUN_4bd03960"
POINT = "mgPoint_c.restore"
VECTOR = "mgVector_c.restore"
XFORM = "mgXform_c.restore"
POINT_OP = "mgPoint_c.operator>>"
XFORM_OP = "mgXform_c.operator>>"
LW3 = "utLineWidth_c.Serialize.3.0"
LW0 = "utLineWidth_c.Serialize0"
OBLIST = "rf.suObList"
OBARRAY = "rf.suObArray"

HIERARCHY = {
    "sgDim": "Dimension_c",
    "sgValDim": "sgDim",
    "sgLogDim": "sgDim",
    "sgValG1Dim": "sgValDim",
    "sgValG2Dim": "sgValDim",
    "sgValG3Dim": "sgValDim",
    "sgOffsetDim": "sgValDim",
    "sgCircularPattCntDim": "sgValDim",
    "sgLinearPattCntDim": "sgValDim",
    "sgSkOffsetDim": "sgOffsetDim",
    "sgCircleDim": "sgValG1Dim",
    "sgConicRhoDim": "sgValG1Dim",
    "sgLoopLengthDim": "sgValG1Dim",
    "sgPipeDim": "sgValG1Dim",
    "sgSameCircleDim": "sgValG1Dim",
    "sgSplineLengthDim": "sgValG1Dim",
    "sgSplineTanMagnitudeDim": "sgValG1Dim",
    "sgAnglDim": "sgValG2Dim",
    "sgBsOrdDim": "sgValG2Dim",
    "sgBsOrdHDim": "sgBsOrdDim",
    "sgBsOrdVDim": "sgBsOrdDim",
    "sgBeltTractionDim": "sgValG3Dim",
    "sgLogG1Dim": "sgLogDim",
    "sgLogG2Dim": "sgLogDim",
    "sgLogG3Dim": "sgLogDim",
    "sgLogGroupDim": "sgLogDim",
    "moFeatureDim_c": "Dimension_c",
    "moRefDim_c": "Dimension_c",
    "moRefDim1E_c": "moRefDim_c",
    "moRefDim2E_c": "moRefDim_c",
    "ParallelPlaneDistanceDim_c": "moFeatureDim_c",
    "ThreeDRadiusDim_c": "moFeatureDim_c",
    "ThreeDdiameterDim_c": "moFeatureDim_c",
    "moNumberDim_c": "moFeatureDim_c",
    "moScalerDim_c": "moFeatureDim_c",
    "AngleDim_c": "moFeatureDim_c",
    "moModDimHandle_c": "moDimHandle_c",
    "moSkDimHandle_c": "moDimHandle_c",
    "moFeatureDimHandle_c": "moModDimHandle_c",
    "moRefDimHandle_c": "moModDimHandle_c",
    "moSkDimHandleValG1_c": "moSkDimHandle_c",
    "moSkDimHandleRadial_c": "moSkDimHandleValG1_c",
    "moSkDimHandleValG2_c": "moSkDimHandle_c",
    "moSkDimHandleOffset_c": "moSkDimHandle_c",
    "moSkDimHandleLinearPattCnt_c": "moSkDimHandle_c",
    "moSkDimHandleCircularPattCnt_c": "moSkDimHandle_c",
    "moDisplayItem_c": "moDisplayObject_c",
    "moDisplayDim_c": "moDisplayItem_c",
    "moDisplayDistanceDim_c": "moDisplayDim_c",
    "moDisplayRadialDim_c": "moDisplayDim_c",
    "moDisplayArcDim_c": "moDisplayDim_c",
    "moDisplayAngularDim_c": "moDisplayArcDim_c",
    "moDisplayRevolveDim_c": "moDisplayRadialDim_c",
    "moDisplayLinearPattCntDim_c": "moDisplayDim_c",
    "moDisplayCircularPattCntDim_c": "moDisplayDim_c",
    "moDoubleParameter_c": "moParameter_c",
    "moLengthParameter_c": "moDoubleParameter_c",
    "moScalerParameter_c": "moDoubleParameter_c",
    "moAngleParameter_c": "moDoubleParameter_c",
    "moIntegerParameter_c": "moParameter_c",
}

DISPLAY_VT = {
    "moDisplayDim_c": (0, 0, 0),
    "moDisplayDistanceDim_c": (1, 0, 0),
    "moDisplayRadialDim_c": (1, 1, 0),
    "moDisplayArcDim_c": (1, 0, 0),
    "moDisplayAngularDim_c": (1, 0, 0),
    "moDisplayRevolveDim_c": (1, 1, 0),
    "moDisplayLinearPattCntDim_c": (0, 0, 0),
    "moDisplayCircularPattCntDim_c": (0, 0, 0),
}


def flag(name):
    return lambda s, ar: s[name] != 0


def signed_count(name):
    return lambda s, ar: max(s[name], 0)


def sum_count(name):
    return lambda s, ar: max(sum(item["v"] for item in s[name]), 0)


def serialize_ptr(name):
    return [i32(f"has_{name}"), If(flag(f"has_{name}"), [obarray(name)])]


def no_cond(mask):
    return lambda s, ar: not has_condition(ar, mask)


def vtv(slot, o):
    table = VT.get(slot, {})
    if o.cls not in table:
        raise ArchiveError(f"no vtable entry {slot:#x} for {o.cls}")
    return table[o.cls]


class ObjIf(Op):
    def __init__(self, pred, then, other=()):
        self.pred, self.then, self.other = pred, list(then), list(other)

    def load(self, ar, scope, o):
        run_load(self.then if self.pred(o, scope, ar) else self.other, ar, scope, o)

    def store(self, ar, scope, o):
        run_store(self.then if self.pred(o, scope, ar) else self.other, ar, scope, o)


def is_dimension(name):
    def pred(s, ar):
        v = s.get(name)
        return v is not None and isa(v.cls, "Dimension_c")
    return pred


def handle_has_gfr(s, ar):
    return s.get("fe8") is not None


def handle_points(s, ar):
    return bool(ar.ctx.get("owner_is_drawing", 0)) or s.get("cond1_flag", 0) != 0


def sk_handle_normal(s, ar):
    return not has_condition(ar, 6) and (not has_condition(ar, 1) or bool(ar.ctx.get("ctx874", 0)))


def sk_handle_virtual(s, ar):
    return has_condition(ar, 1) and not ar.ctx.get("ctx874", 0)


def dispobj_link_read(s, ar):
    return s.get("ff8") is None or not has_condition(ar, 0x8001)


def dispobj_linked(s, ar):
    if dispobj_link_read(s, ar):
        return s["linked"] if ver(ar) > 0xDFD else 0
    if not has_condition(ar, 0x8000):
        return 1
    return s["linked"]


def pointref_block(o, s, ar):
    if not vtv(0xA78, o):
        return False
    if ver(ar) <= 0x16B or has_condition(ar, 2):
        return False
    a8, d8 = vtv(0x8A8, o), vtv(0x8D8, o)
    if not d8 and not a8:
        return True
    if a8 and ver(ar) > 0x467:
        return True
    return bool(d8) and ver(ar) > 0x233


def define_helpers(reg):
    reg.provisional(POINT, [f64("x"), f64("y"), f64("z")])
    reg.provisional(VECTOR, [f64("x"), f64("y"), f64("z")])
    reg.provisional(POINT_OP, [f64("x"), f64("y"), f64("z")])
    reg.provisional("mgPerspInfoBase_c.restore", [f64(f"p{k}") for k in range(4)])
    reg.provisional("mgPerspInfo_c.restore", [f64(f"p{k}") for k in range(6)])
    reg.provisional("mgMatrix5_c.restore", [i32("dim")] + [f64(f"m{k}") for k in range(25)])
    reg.provisional(XFORM_OP, [
        Rep(lambda s, ar: 30, "words", [u32("w")]),
        If(lambda s, ar: s["words"][28]["w"] & 0xF0 == 0x10, [emb("persp", "mgPerspInfoBase_c.restore")]),
        If(lambda s, ar: s["words"][28]["w"] & 0xF0 == 0x20, [emb("persp", "mgPerspInfo_c.restore")]),
        If(lambda s, ar: s["words"][28]["w"] & 0xF0 == 0x40, [emb("persp", "mgMatrix5_c.restore")]),
    ])
    reg.provisional(LW3, [Vge(0xF41, [i16("f06"), f32("f00")], [i32("f06")])])
    reg.provisional(LW0, [Vge(0xF41, [i16("f06"), f32("f00")])])
    reg.define(DYNARRAY, [
        u32("elem"),
        If(flag("elem"), [
            u32("alloc_a"),
            u32("alloc_b"),
            u32("n"),
            Raw("data", lambda s, ar: s["n"] * s["elem"]),
        ]),
    ])


def define_dimensions(reg):
    reg.define(DIMENSION, [
        i32("refcount"),
        xo("f28"),
        xo("f48", "moDimTolerance_c"),
        Vge(0x335, [i32("f50")]),
        Vgt(0x801, [i32("f30")]),
        Vge(0x90A, [i32("f54")]),
        Vgt(0xDDD, [i32("f5c")]),
        Vgt(0xFB1, [xo("f60", "moAttachPoint_c")]),
        Vge(0x2392, [u16("f68")]),
        Vgt(0x42EE, [u8("has_f78"), If(flag("has_f78"), [cstr("f78")])]),
        Cnd(7, [i32("cond_f34")]),
    ])
    reg.define(FEATURE_DIM, [
        base(DIMENSION),
        emb("f80", POINT),
        emb("fa0", POINT),
        emb("fc0", POINT),
        Vgt(0xE3, [u16("has_fe0"), If(flag("has_fe0"), [emb("fe0", VECTOR), emb("fe8", VECTOR)])]),
        Vgt(0x12D, [
            u16("has_ff0"),
            If(flag("has_ff0"), [Vlt(0x3A6, [Legacy("mgXform_c::restoreAsIs pre-0x3a6")], [emb("ff0", XFORM)])]),
        ]),
        Vgt(0x4AB, [u16("pt_flags")]),
        If(lambda s, ar: s.get("pt_flags", 0) & 1, [emb("f98", POINT)]),
        If(lambda s, ar: s.get("pt_flags", 0) & 2, [emb("fb8", POINT)]),
    ])
    for c in ("ParallelPlaneDistanceDim_c", "ThreeDRadiusDim_c", "ThreeDdiameterDim_c", "moNumberDim_c", "moScalerDim_c"):
        reg.define(c, [base(FEATURE_DIM)])
    reg.define("AngleDim_c", [base(FEATURE_DIM), Vge(0x2DD, [u16("ff8")])])
    reg.define(REF_DIM, [
        base(DIMENSION),
        emb("f80", XFORM),
        Vgt(0x98, [
            u8("has_f88"),
            If(flag("has_f88"), [emb("f88", VECTOR)]),
            u8("has_f90"),
            If(flag("has_f90"), [emb("f90", VECTOR)]),
        ]),
        Vgt(0x22C, [i32("fa4"), xo("fa8", "moDimPlaneEntTag_c"), i32("fb0")]),
        Vge(0x426, [xo("fb8")]),
        Vgt(0x4E9, [i32("fa0")]),
        Vgt(0xAA9, [i32("fc4")]),
        Vgt(0xE32, [i32("fc8")]),
        Vgt(0x46C6, [i32("fd0")]),
    ])
    reg.define("moRefDim2E_c", [
        base(REF_DIM),
        u16("fd8"),
        xo("fe0"),
        Vin(0x141, 0x15A, [xo("old_fe0_tag", "moDrViewTag_c")]),
        u16("ff0"),
        xo("ff8"),
        Vin(0x141, 0x15A, [xo("old_ff8_tag", "moDrViewTag_c")]),
        u16("f108"),
        Vge(0xCE, [u16("f110"), u16("f114")]),
        Vge(0x2DD, [u16("f118")]),
        Vgt(0x727, [u16("f11c")]),
        Vgt(0x3747, [u16("f10c")]),
    ])
    reg.define("moDimTolerance_c", [
        i32("f08"),
        Vgt(0x98C, [i32("f0c")]),
        f64("f10"),
        f64("f18"),
        Vgt(0x155, [u8("f78"), f64("f80"), Vge(0x3CF, [f64("f88")]), f64("f90")]),
        Vgt(0x232, [cstr("f20"), cstr("f28")]),
        Vgt(0x71A, [u8("f48"), Vlt(0x768, [u8("f50")])]),
        Vge(0x768, [i32("f58"), u8("f98"), f64("fa0"), f64("fa8"), f64("fb0")]),
        Vge(0x7F9, [u8("f5c"), u8("f60")]),
        Vge(0x23D3, [i32("fb8")]),
        Vgt(0x2B6D, [cstr("f30"), cstr("f38"), cstr("f40")]),
        Vgt(0x2B76, [i32("fbc")]),
    ])


def define_handles(reg):
    reg.define(DIM_HANDLE, [
        base("moCompRef_c"),
        Vgt(299, [u16("has_f120"), If(flag("has_f120"), [emb("f120", XFORM)])]),
        Vgt(0x159, [xo("f130", "moDrViewTag_c"), xo("f138", "moDrViewTag_c")]),
        Vgt(0xCD9, [xo("f140", "moDrViewTag_c"), xo("f148", "moDrViewTag_c")]),
        Vgt(0x216, [u8("f150")]),
        Vgt(0x321, [xo("fe8", "moGFR_c")]),
        Vgt(0x4A9, [
            xo("f100"),
            If(is_dimension("f100"), [
                emb("f108", XFORM),
                Vgt(0x4E8, [i32("has_f110"), If(flag("has_f110"), [cstr("f110")])]),
            ]),
        ]),
        Vgt(0xFC1, [i32("f154")]),
        Vgt(0x11BD, [u16("has_f128"), If(flag("has_f128"), [emb("f128", XFORM)])]),
        Vge(0x335D, [
            Cnd(1, [i32("cond1_flag")]),
            If(handle_points, [emb("f180", POINT), emb("f198", POINT), emb("f1b0", POINT), emb("f1c8", POINT)]),
        ]),
        Vgt(0x12FF, [i32("f118")]),
    ])
    reg.define(MOD_HANDLE, [
        base(DIM_HANDLE),
        Cnd(1, [Legacy("moModDimHandle_c condition 1 vtable 0x738")]),
        Vlt(0x322, [u8("old_has_ext"), If(flag("old_has_ext"), [Legacy("moModDimHandle_c external object pre-0x322")])]),
        If(handle_has_gfr, [], [xo("ff0")]),
    ])
    reg.define(SK_HANDLE, [
        base(DIM_HANDLE),
        If(sk_handle_virtual, [Legacy("moSkDimHandle_c condition 1 vtable 0x778")]),
        If(sk_handle_normal, [
            Vlt(0x322, [u8("old_has_ext"), If(flag("old_has_ext"), [Legacy("moSkDimHandle_c external object pre-0x322")])]),
            If(handle_has_gfr, [Vge(0xD7, [u16("dim_type")])], [xo("ff0", "sgSketch")]),
            i32("ff8"),
        ], [
            i32("ff0"),
            i32("ff8"),
        ]),
    ])
    for c in ("moFeatureDimHandle_c", "moRefDimHandle_c"):
        reg.define(c, [base(MOD_HANDLE)])
    for c in ("moSkDimHandleRadial_c", "moSkDimHandleValG2_c", "moSkDimHandleOffset_c",
              "moSkDimHandleLinearPattCnt_c", "moSkDimHandleCircularPattCnt_c"):
        reg.define(c, [base(SK_HANDLE)])


def define_display(reg):
    reg.provisional(DISPLAY_OBJECT, [
        Cnd(1, [Legacy("moDisplayObject_c suDataLocationId_c")]),
        u16("f50"),
        xo("f30"),
        xo("f40"),
        xo("f48"),
        Vgt(0x2F7, [i32("f54")]),
        Vgt(0x4EC, [i32("f11c")]),
        Vgt(0x44D, [emb("f08", "moEntVisProp_c")]),
        Vgt(0x749, [Cnd(1, [], [emb("f68", OBLIST), emb("fb0", OBLIST)])]),
        Vgt(0x71C, [i32("f58")]),
        Vgt(0xA02, [xo("ff8", "moLinkedDispObjArray_c")]),
        If(dispobj_link_read, [Vgt(0xDFD, [i32("linked")])], [Cnd(0x8000, [i32("linked")])]),
        If(no_cond(0x10000000), [
            If(lambda s, ar: dispobj_linked(s, ar) != 0, [
                i32("n138"),
                If(lambda s, ar: s["n138"] >= 1, [emb("f138", OBLIST)]),
            ]),
        ], [
            If(lambda s, ar: s.get("ff8") is not None, [Legacy("moDisplayObject_c FUN_4ba53a40")]),
        ]),
        Vge(0xF9C, [i32("f118")]),
    ])
    reg.provisional(DISPLAY_ITEM, [
        Vlt(0x2F2, [Legacy("moDisplayItem_c pre-0x2f2")], [base(DISPLAY_OBJECT)]),
        Vgt(0x1F8, [i32("f390")]),
        Vgt(0x20E, [i32("f3e0")]),
        Vgt(0x20F, [emb("f290", POINT)]),
        Vgt(0x211, serialize_ptr("f298")),
        Vge(0x64D, [i32("has_f288"), If(flag("has_f288"), [emb("f288", OBLIST)])]),
        Vin(0x65B, 0x669, [xo("old_65b")]),
        Vgt(0xA10, [xo("f3f8", "moCompFeature_c")]),
        Vgt(0xA57, [emb("f400", VECTOR)]),
        Vgt(0xB79, [
            emb("f2a0", XFORM),
            i32("n2b0"),
            Rep(signed_count("n2b0"), "f2b0", [i32("v")]),
        ]),
        Vgt(0xBE0, [u8("has_f2c0"), If(flag("has_f2c0"), [emb("f2c0", VECTOR)])]),
        Vgt(0xBEE, [f64("f2c8"), i32("has_f2d0"), If(flag("has_f2d0"), [emb("f2d0", XFORM)])]),
        Vgt(0xC70, [i32("n3d0"), Rep(signed_count("n3d0"), "f3c0", [xo("o")])]),
        Vgt(0xD7A, [xo("f2d8")]),
        Vgt(0xD99, [f64("f3b8")]),
        Vlt(0xE60, [
            Vgt(0xDE4, [f64(f"old_arrow{k}") for k in range(6)]),
        ], [
            u32("n2e8"),
            Rep("n2e8", "f2e0", [i32("k"), xo("v", "moArrowSize_c")]),
        ]),
        Vge(0xF20, [
            i32("f2f0"),
            emb("f2f8", LW3),
            Vlt(0xF41, [f64("old_f20_d")]),
            i32("f2f4"),
            i32("f304"),
            emb("f30c", LW3),
            Vlt(0xF41, [i32("old_f20_i")]),
            i32("f308"),
        ]),
        Vgt(0xF45, [i32("f300"), i32("f314"), i32("f334"), i32("f338")]),
        Cnd(1, [], [Vge(0x106F, serialize_ptr("f4a0"))]),
        Vge(0x1820, [
            i32("f318"),
            i32("f31c"),
            emb("f320", LW0),
            i32("f328"),
            Vlt(0x1829, [u32("old_1829a"), u32("old_1829b")]),
            i32("f32c"),
        ]),
        Vin(0x1BE2, 0x1BF9, [i32("old_1be2")]),
        Vgt(0x1BF8, [
            u32("n4a8"),
            Rep("n4a8", "f4a8", [i32("k"), xo("v", "moSplineLeaderData_c")]),
        ]),
        Vgt(0x277C, [i32("has_f4b8"), If(flag("has_f4b8"), [Legacy("moWatermarkNoteData_c::Serialize")])]),
        Vgt(0x3371, [
            i32("n4f0"),
            If(lambda s, ar: s["n4f0"] < 5, [
                Rep(signed_count("n4f0"), "f4f0", [emb("p", POINT)]),
                Vlt(0x3374, [emb("old_f550", VECTOR)], [
                    i32("n550"),
                    If(lambda s, ar: s["n550"] < 3, [
                        Rep(signed_count("n550"), "f550", [emb("v", VECTOR)]),
                    ], [Legacy("moDisplayItem_c vector count >= 3")]),
                ]),
            ], [Legacy("moDisplayItem_c point count >= 5")]),
        ]),
    ])
    reg.define(DISPLAY_DIM, [
        Vlt(0x237, [Legacy("moDisplayDim_c pre-0x237")], [base(DISPLAY_ITEM)]),
        emb("f6a0", "moDimText_c"),
        Vgt(0x65, [Vlt(0xBB, [Legacy("moDisplayDim_c text pair pre-0xbb")])]),
        Vlt(0x728, [xo("old_f850")], [i32("n850"), Rep(signed_count("n850"), "f850", [xo("o")])]),
        Vlt(0x250, [u16("old_250a")]),
        Vlt(0x231, [u16("old_231a")]),
        Vlt(0x15F, [u16("old_15f")]),
        Vlt(0x231, [u16("old_231b")]),
        u16("f870"),
        Vge(0x48C, [u16("f874")]),
        u16("f878"),
        Vgt(0xBA, [
            cstr("f7f8"),
            cstr("f800"),
            Vgt(0x1AC, [cstr("f818"), cstr("f820")]),
            Vlt(0x231, [u8("old_231c")]),
        ]),
        emb("f880", VECTOR),
        Vlt(0x8E, [f64("old_8e")]),
        f64("f8a8"),
        Vlt(0x46, [f64("old_46a"), f64("old_46b")]),
        f64("f8b0"),
        Vlt(0x250, [f64("old_250d")]),
        Vlt(0x46, [f64("old_46c"), f64("old_46d"), f64("old_46e")]),
        f64("f950"),
        Vge(0x48A, [f64("fa78")]),
        Vlt(0x250, [emb("old_250v", VECTOR)]),
        emb("f958", POINT),
        emb("f970", POINT),
        emb("f988", POINT),
        emb("f9a0", POINT),
        emb("f9b8", POINT),
        Vgt(0x38E, [
            i32("has_fa50"),
            If(flag("has_fa50"), [emb("fa50_p", POINT), emb("fa50_v", VECTOR), f64("fa50_d")]),
        ]),
        Vgt(0x3C, [u16("f898"), u16("f89c"), u16("f8a0")]),
        Vgt(0x74, [
            u16("f8c0"),
            Vlt(0x231, [u8("old_74a")]),
            u16("f8e4"),
            u16("f8ec"),
            Vlt(0x231, [u8("old_74b")]),
        ]),
        Vgt(0x84, [Vlt(0x250, [f64("old_84")])]),
        Vgt(0xB6, [u16("f8f4")]),
        Vgt(0x12D, [emb("fa38", VECTOR)]),
        ObjIf(pointref_block, [
            xo("f580", "moPointRef_w"),
            xo("f588", "moPointRef_w"),
            Vgt(0x24F, [f64("f5a0"), f64("f5a8")]),
            Vgt(0x4E2, [
                i32("has_f590"),
                If(flag("has_f590"), [emb("f590", POINT)]),
                i32("has_f598"),
                If(flag("has_f598"), [emb("f598", POINT)]),
            ]),
        ]),
        Vge(0x1D5, [u16("f8e8"), u16("f8f0"), Vlt(0x231, [u8("old_1d5")])]),
        Vgt(0x230, [u32("f8a4")]),
        If(no_cond(6), [Vgt(0x225, serialize_ptr("fa58"))]),
        If(no_cond(6), [Vgt(0x309, serialize_ptr("fa60"))]),
        Vgt(0x2D5, [Vlt(0x2DA, [xo("old_fa68", "moAlignGroup_c")], [cstr("fa70")])]),
        Vgt(0x3A8, [xo("faf8", "moLengthUserUnits_c"), xo("fb00", "moAngleUserUnits_c")]),
        Vge(0x449, [i32("f8f8")]),
        Vgt(0x4DA, [f64("fad0")]),
        Vgt(0x74B, [emb("f5b0", DYNARRAY)], [Vge(0x4DB, [f64("old_f5b0")])]),
        Cnd(5, [i32("faf0")]),
        Vgt(0x725, [cstr("f680"), xo("f688")]),
        Vgt(0x737, [f64("fb40")]),
        Vge(0x7F4, [u16("fb68"), u16("fb6c")]),
        Vge(0x883, [u32("fb60")]),
        Vlt(0x11F4, [
            Vgt(0x9F7, [f64("f830"), f64("f840"), i32("faf4")]),
        ], [
            f64("f830"), f64("f838"), f64("f840"), f64("f848"), i32("faf4"),
        ]),
        Vgt(0xAE6, [f64("f8b8")]),
        Vgt(0xB47, [u16("f8fc")]),
        Vgt(0xCF0, [i32("f900")]),
        Vgt(0xB85, [emb("f5c0", XFORM_OP), f64("f648")]),
        Vlt(0x11F4, [
            Vgt(0xBE2, [cstr("fb70"), cstr("fb80")]),
        ], [
            cstr("fb70"), cstr("fb78"), cstr("fb80"), cstr("fb88"),
        ]),
        Vgt(0xC9A, [Cnd(0x8000, [], [emb("fe48", OBARRAY)])]),
        Vgt(0xCE6, [emb("f908", OBLIST)]),
        Vgt(0xDD9, [i32("fb9c")]),
        Vgt(0xE40, [u32("fe40")]),
        Vgt(0xF0B, [xo("fa80", "moDimJog_c"), xo("fa88", "moDimJog_c")]),
        Vgt(0xF4E, [xo("fba0", "moDisplayDim_c")]),
        Vge(0xF60, [u32("fb64")]),
        Vgt(0xF9D, [
            xo("fab0", "moDrViewTag_c"),
            xo("fab8", "moDrViewTag_c"),
            i32("has_fac0"),
            If(flag("has_fac0"), [emb("fac0", POINT)]),
            i32("has_fac8"),
            If(flag("has_fac8"), [emb("fac8", POINT)]),
        ]),
        Vgt(0xFAD, [i32("fa90")]),
        Vgt(0x12C2, [xo("fef8")]),
        Vge(0x13F3, [i32("fb4c"), i32("fb50")]),
        Vge(0x1405, [i32("fd78"), i32("fd7c")]),
        Vgt(0x140E, [i32("ff00")]),
        Vgt(0x1464, [f64("f8c8")]),
        Vgt(0x17D6, [i32("f8d0")]),
        Vgt(0x1815, [i32("ff08"), i32("ff0c"), i32("ff10")]),
        Vgt(0x1828, [i32("f8d8"), i32("f8dc")]),
        Vgt(0x182C, [cstr("f808")]),
        Vgt(0x182F, [cstr("f810")]),
        Vgt(0x1843, [i32("fd80")]),
        Vgt(0x1FA6, [i32("ff84")]),
        Vgt(0x1FBB, [i32("ff54"), cstr("ff60"), i32("f650"), i32("ff80"), emb("ff68", POINT_OP)]),
        Vgt(0x1FC2, [i32("ff58")]),
        Vgt(0x23AE, [i32("f8e0")]),
        Vge(0x27E0, [cstr("ff88")]),
        Vgt(0xDD6, [Vlt(0xDE5, [f64(f"old_dd6_{k}") for k in range(6)])]),
    ])
    reg.define(RADIAL, [
        base(DISPLAY_DIM),
        Vgt(0x3C6, [i32("ffd8")], [Vge(0xB1, [u8("old_ffd8")])]),
        Vgt(0x219, [f64("ffe0"), f64("ffe8"), f64("fff0"), f64("fff8"), f64("f1000"), f64("f1008")]),
        Vgt(0x270, [emb("f1010", POINT), emb("f1028", POINT)]),
        Vge(0x2F3, [i32("nfc0"), Rep(signed_count("nfc0"), "ffc0", [cstr("s")])]),
        Vgt(0x4A7, [Vlt(0x4B7, [i32("old_4a7a"), i32("old_4a7b")])]),
        Vgt(0x83D, [Vlt(0x86D, [xo("old_f1050")], [xo("f1050", "moHwCalloutData_c")])]),
        Vgt(0x92C, [Vlt(0x964, [u16("old_92c")])]),
        Vgt(0x938, [cstr("f1048")]),
        Vgt(0xA7A, [Vlt(0xA9A, [Legacy("moDisplayRadialDim_c FUN_4c78c320 pre-0xa9a")])]),
        Vgt(0xB85, [xo("f1068", "suObList")]),
        If(lambda s, ar: ver(ar) == 0xB9E, [
            f64("old_b9e_d"),
            emb("old_b9e_v", VECTOR),
            emb("old_b9e_p", POINT_OP),
            i32("old_b9e_i"),
        ]),
        Vgt(0xBE5, [i32("has_f1060"), If(flag("has_f1060"), [emb("f1060", XFORM)])]),
        Vgt(0x11F8, [xo("f1090", "moMirrorHWHelper_c")]),
        Vgt(0x23AA, [i32("ffd4")]),
        Vgt(0x333D, [xo("f10a8", "moHoleWizardInfo_c")]),
        Vgt(0x3B21, [i32("f10a4")]),
    ])
    reg.define(ARC, [
        base(DISPLAY_DIM),
        u16("f100c"),
        u16("f1010"),
        Vgt(0x60, [
            u8("f1008"),
            emb("ffb8", VECTOR),
            emb("ffd0", VECTOR),
            f64("ffe8"), f64("fff0"), f64("fff8"), f64("f1000"),
        ]),
        Vgt(0x4DE, [i32("f1018")]),
    ])
    for c in ("moDisplayDim_c", "moDisplayLinearPattCntDim_c", "moDisplayCircularPattCntDim_c"):
        reg.define(c, [base(DISPLAY_DIM)])
    reg.define("moDisplayRadialDim_c", [base(RADIAL)])
    for c in ("moDisplayArcDim_c", "moDisplayAngularDim_c"):
        reg.define(c, [base(ARC)])
    reg.define("moDisplayDistanceDim_c", [
        base(DISPLAY_DIM),
        Vgt(0x272, [i32("f1014")]),
        Vgt(0xB2E, [f64("ffb8"), f64("ffc0"), emb("ffe8", POINT_OP), i32("f1000")]),
        Vgt(0xB85, [Cnd(2, [i64("f1008")], [xo("f1008", "moDisplayRadialDim_c")])]),
        Vgt(0x3747, [i32("f1010")]),
    ])
    reg.define("moDisplayRevolveDim_c", [
        Vgt(0x4BA, [base(RADIAL)], [base(DISPLAY_DIM)]),
        Vge(0x4B7, [
            i32("f1140"),
            emb("f1148", VECTOR),
            emb("f1160", VECTOR),
            f64("f1178"), f64("f1180"), f64("f1188"), f64("f1190"),
            emb("f1198", XFORM),
            i32("f1220"),
        ]),
    ])
    reg.define("moDimText_c", [
        cstr("f08"),
        emb("f38", POINT),
        Vlt(0x3F, [Legacy("moDimText_c pre-0x3f")], [
            i32("f10"),
            xo("f18", "utCharFormat_c"),
            Vlt(0x1AE, [Legacy("moDimText_c pre-0x1ae")], [Vge(0x31B, [i32("f20")])]),
            emb("f50", POINT),
            f64("f68"),
            i32("n90"),
            If(lambda s, ar: s["n90"] > 0, [
                Rep("n90", "f98", [i32("v")]),
                Rep(sum_count("f98"), "f88", [i32("v")]),
                Rep(sum_count("f98"), "f80", [i32("v")]),
                Rep(sum_count("f80"), "f78", [emb("p", POINT)]),
            ]),
            Vge(0x740, [i32("fc4")]),
        ]),
        Vge(0x725, [
            i32("fa0"),
            If(flag("fa0"), [
                i32("na4"),
                Rep(signed_count("na4"), "fa8", [emb("p", POINT)]),
                Rep(signed_count("na4"), "fb0", [i32("v")]),
                Rep(signed_count("na4"), "fb8", [emb("v", VECTOR)]),
                i32("fc0"),
            ]),
            Vgt(0x72A, [i32("fd0"), f64("fd8"), f64("fe0")]),
            Vgt(0x809, [i32("f24")]),
        ]),
        Vgt(0x990, [emb("f0f0", "su_CStringArray"), i32("f118")]),
        Vgt(0xD8D, [i32("f120")]),
        Vgt(0xDA9, [i32("f124"), f64("f128"), i32("f130")]),
    ])


def define_parameters(reg):
    reg.define(PARAM, [
        base("moNode_c"),
        Vlt(0x218, [xo("old_units")]),
        Vgt(0x6A, [Vlt(0xDB9, [i32("old_6a")]), xo("f48", "moNodeName_c")]),
        Vgt(0xA9C, [Vlt(0xDB9, [i32("old_a9c")])]),
    ])
    reg.define(DOUBLE_PARAM, [
        base(PARAM),
        f64("f58"),
        Cnd(0x80, [], [Vgt(0x3DA, [u8("f68"), If(flag("f68"), [f64("f60")])])]),
    ])
    reg.define("moScalerParameter_c", [base(DOUBLE_PARAM)])
    reg.define("moLengthParameter_c", [base(DOUBLE_PARAM)])
    reg.define("moAngleParameter_c", [base(DOUBLE_PARAM), Vlt(0x2DD, [u16("old_2dd")])])
    reg.define("moIntegerParameter_c", [
        base(PARAM),
        i32("f58"),
        Cnd(0x80, [], [Vgt(0x3DA, [u8("f60"), If(flag("f60"), [i32("f5c")])])]),
    ])


def define_misc(reg):
    reg.define(EXT_SKETCH, [
        If(no_cond(7), [xo("f08", "sgSketch")]),
    ])
    reg.define("moExtensionLineIndicator_c", [
        base(EXT_SKETCH),
        Vgt(0xE57, [u16("f18")], [Legacy("moExtensionLineIndicator_c sgEntHandle list pre-0xe58")]),
    ])


def define(reg):
    for c, p in HIERARCHY.items():
        PARENT.setdefault(c, p)
    for c, (a78, d8, a8) in DISPLAY_VT.items():
        vt(0xA78, c, a78)
        vt(0x8D8, c, d8)
        vt(0x8A8, c, a8)
    for c in ("moScalerParameter_c", "moLengthParameter_c", "moAngleParameter_c", "moIntegerParameter_c"):
        node_vt(c)
    define_helpers(reg)
    define_dimensions(reg)
    define_handles(reg)
    define_display(reg)
    define_parameters(reg)
    define_misc(reg)
