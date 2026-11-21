from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, ver, i32, u32, u16, i16, u8, f64, f32, i64, cstr, emb, base, count
from Schema import If, Rep
from defs.ResolvedCore import xo, Legacy, Cnd, Ctx, Vin, PARENT, has_condition

ENT = "sk.sg2DEnt.FUN_4c583460"
SEG = "sk.sgSegment.FUN_4c590920"
POINT = "sk.sgPoint.FUN_4c58f910"
LINE = "sk.sgLine.FUN_4c58ac90"
ARC = "sk.sgArc.FUN_4c585150"
ELLIPSE = "sk.sgEllipse.FUN_4c586da0"
PARABOLA = "sk.sgParabola.FUN_4c586080"
SPLINE = "sk.sgSpline.FUN_4c59aed0"
SPLINE_STYLE = "sk.sgSpline.FUN_4c59aed0.vt1f0"
SPLINE_8E00 = "sk.sgSpline.FUN_4c3f8e00"
SPLINE_5860 = "sk.sgSpline.FUN_4b975860"
TEXT = "sk.sgText.FUN_4c59de50"
HATCH = "sk.sgHatch.FUN_4c5888a0"
PLANE3D = "sk.sg3DPlane.FUN_4c5845b0"
CONE3D = "sk.sg3DCone.FUN_4c5841b0"
OFFSET = "sk.sgOffset_c.FUN_4c58d9a0"
SKOFFSET = "sk.sgSketchOffset_c.FUN_4c599eb0"
STYLED = "sk.sgStyledCurve.FUN_4c59d6c0"
INTERSECTION = "sk.sgIntersection_c.FUN_4c5895f0"
SILHOUETTE = "sk.sgSilhouette_c.FUN_4c590d90"
DIMS = "sk.sgSketch.FUN_4c5a0f00"
CREATION = "sk.sgCreationIDs.FUN_4c5864f0"
COINC = "sk.pnt3DcoincMap_c.FUN_4b9611e0"
RELMGR = "sk.moSketchRelMgr_c.FUN_4c6035c0"
EQMAP = "sk.EquationVarValueMap_c.FUN_4c339ca0"
BLOCKMGR = "sk.sgBlockManager.FUN_4c90b810"
HDATAMGR = "sk.sgEntHandleDataManager_c.FUN_4c90bf80"
LOOPMGR = "sk.sgLoopManager.FUN_4c58cf30"
SLOTMGR = "sk.sgSlotManager_c.FUN_4c59a5f0"
HANDLE = "sk.sgEntHandle.Serialize"
DIMENSION = "Dimension_c.Serialize"
SGDIM = "sk.sgDim.FUN_4c5868d0"
LOGDIM = "sk.sgLogDim.Serialize"
LOG_G1 = "sk.sgLogG1Dim.Serialize"
LOG_G2 = "sk.sgLogG2Dim.FUN_4c58b970"
LOG_G3 = "sk.sgLogG3Dim.Serialize"
LOG_GROUP = "sk.sgLogGroupDim.Serialize"
ISO = "sk.sgIsoParam_c.FUN_4c58a910"
LIN_PATT = "sk.sgLinearPattern.FUN_4c58adf0"
PATT_CON = "sk.sgPattCon.FUN_4c58f060"
CIRC_PATT = "sk.sgCircularPattern.FUN_4c5856e0"
DIM_7C0 = "sk.FUN_4b9787c0"
DIM_9F0 = "sk.FUN_4b9789f0"
VALDIM = "sk.sgValDim.FUN_4c59ea80"
VAL_G1 = "sk.sgValG1Dim.FUN_4c59ec10"
VAL_G2 = "sk.sgValG2Dim.FUN_4c59f080"
VAL_G3 = "sk.sgValG3Dim.FUN_4c59f730"
XFORM_OP = "mgXform_c.operator>>"
LINEVIZ = "moLineViz_c.Serialize.0"
LW3 = "utLineWidth_c.Serialize.3.0"

HANDLES = (
    "sgEntHandle", "sgPointHandle", "sgLineHandle", "sgArcHandle", "sgSegmentHandle", "sgEllipseHandle",
    "sgParabolaHandle", "sgConicHandle", "sgSplineHandle", "sgTextHandle", "sgHatchHandle", "sgFrameHandle",
    "sgSlotHandle", "sgSketchBlockHandle", "sg3DPlaneHandle", "sg3DSurfaceHandle", "sg3DCylinderHandle",
    "sg3DSphereHandle", "sg3DConeHandle", "sg3DParametricSurfaceHandle",
)
VAL_G1_SCOPE = ("sgCircleDim",)
VAL_G1_OTHER = ("sgValG1Dim", "sgConicRhoDim", "sgLoopLengthDim", "sgPipeDim", "sgSameCircleDim", "sgSplineLengthDim", "sgSplineTanMagnitudeDim")
VAL_G2_SCOPE = ("sgPntPntDist", "sgLLDist", "sgPntLineDist", "sgPntPntHorDist", "sgPntPntVertDist")
VAL_G2_OTHER = (
    "sgValG2Dim", "sg3DPlane3DPlaneAngle", "sg3DPlane3DPlaneDist", "sg3DPlaneLineAng", "sgBsOrdDim", "sgBsOrdHDim",
    "sgBsOrdVDim", "sgFlangeFaceDist", "sgLine3DPlaneAng", "sgLine3DPlaneDist", "sgPipePipeDist", "sgPipePlaneDist",
    "sgPntLineHorDist", "sgPntLineVertDist", "sgPntPnt3DXDist", "sgPntPnt3DYDist", "sgPntPnt3DZDist", "sgPoint3DPlaneDist",
)
VAL_G3_OTHER = ("sgValG3Dim", "sgArcLenDist", "sgBeltTractionDim", "sgPipePipePlaneDist")


def flag(name):
    return lambda s, ar: s[name] != 0


def bit(name, mask):
    return lambda s, ar: (s[name] & mask) != 0


def nobit(name, mask):
    return lambda s, ar: (s[name] & mask) == 0


def signed_count(name):
    return lambda s, ar: max(s[name], 0)


def owner_1ed8(ar):
    return bool(ar.ctx.get("sketch_owner_1ed8", 0))


def sk_count(name):
    return Vlt(0x2E4, [u16(name)], [i32(name)])


def sk_list(name, items, body):
    return [sk_count(name), Rep(signed_count(name), items, body)]


def u16_list(name, items, body):
    return [u16(name), Rep(name, items, body)]


def idx16(name):
    return [u16(name + "_s"), If(lambda s, ar: s[name + "_s"] == 0xFFFF, [i32(name)])]


def pairmap(name):
    return [i32(name + "_n"), Rep(signed_count(name + "_n"), name, [i32("k"), i32("v")])]


def define_helpers(reg):
    reg.provisional("mgPoint_c.restore", [f64("x"), f64("y"), f64("z")])
    reg.provisional("mgVector_c.restore", [f64("x"), f64("y"), f64("z")])
    reg.provisional("mgPoint_c.restore2D", [f64("x"), f64("y")])
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
    reg.provisional(LINEVIZ, [
        cstr("f08"),
        emb("lw", LW3),
        i32("f10"),
        Vge(0xA80, [i32("f14")]),
    ])
    reg.provisional("moSkIntersectInfo_c", [
        u16("f08"),
        i32("f0c"),
        i32("f10"),
        i32("f14"),
        Vgt(0x264, [i32("f18")]),
    ])
    reg.provisional("moSkIsoCurveInfo_c", [
        f64("f08"),
        u16("f10"),
        u16("f18"),
        Vge(0x66A, [u16("f1c"), i32("f20")]),
        Vge(0x675, [u16("f14")]),
    ])
    reg.provisional(DIMENSION, [
        i32("refcount"),
        Vlt(0x21D, [Legacy("Dimension_c parameter pre-0x21d")], [xo("param")]),
        xo("tolerance"),
        Vge(0x335, [i32("f50")]),
        Vgt(0x801, [i32("f30")]),
        Vge(0x90A, [i32("f54")]),
        Vgt(0xDDD, [i32("f5c")]),
        Vgt(0xFB1, [xo("f60")]),
        Vge(0x2392, [u16("f68")]),
        Vgt(0x42EE, [u8("has_name"), If(flag("has_name"), [cstr("name")])]),
        Cnd(7, [i32("cond_i32")]),
    ])


def define_entities(reg):
    reg.define(ENT, [
        i32("f08"),
        Vgt(0xD2, [i32("f0c")]),
        If(lambda s, ar: ver(ar) > 0x435 and (ver(ar) < 0x511 or not owner_1ed8(ar)), [emb("vis", "moEntVisProp_c")]),
        i32("f20"),
        Vgt(0x4A1, [u16("dflt")]),
        If(lambda s, ar: s.get("dflt", 0) == 0, [
            u16("f30"),
            u16("f34"),
            u16("f38"),
            emb("lw", "utLineWidth_c.Serialize2"),
            Vlt(0xD89, [u16("old_d89")]),
        ]),
        Cnd(2, [i64("ext_ptr")], [xo("ext", "sgExtEnt_c")]),
        If(lambda s, ar: s.get("dflt", 0) == 0, [
            Vgt(0x145, [u16("f54"), Vgt(0x765, [u16("f56")])], [Legacy("sg2DEnt flag words pre-0x146")]),
        ], [
            Vgt(0x513, [u16("f54")]),
            Vgt(0x765, [u16("f56")]),
        ]),
        Vin(0xBDC, 0xBE9, [u16("old_bdc")]),
        Vgt(0x5D, [i32("f50")]),
        If(lambda s, ar: (s.get("f54", 0) & 3) != 3, [
            If(lambda s, ar: ver(ar) > 0xDA and s.get("dflt", 0) == 0, [xo("group", "moGroup")]),
            Vin(0xE3, 0x146, [u16("old_e3")]),
            Vin(0x439, 0x440, [xo("old_layer", "moLayer_c")]),
            Vgt(0xA2B, [u8("has_name"), If(flag("has_name"), [cstr("name")])]),
            Vin(0xA90, 0xAA1, [u16("old_a90")]),
            Vgt(0xD7C, [f64("f68")]),
            Vgt(0x27AB, [u32("f74")]),
            Vgt(0x27C4, [u32("f78")]),
        ]),
    ])
    reg.define(POINT, [
        base(ENT),
        Vlt(0x49C, [Legacy("sgPoint pre-0x49c")], [
            u16("pflags"),
            If(bit("pflags", 0x10), [emb("pos", "mgPoint_c.restore2D")], [emb("pos", "mgPoint_c.restore")]),
            u16("fe4"),
            u16("fe8"),
            If(nobit("pflags", 0x20), [xo("h1", "sgEntHandle"), xo("h2", "sgEntHandle")]),
            u16("fec"),
            If(nobit("pflags", 0x20), [
                i32("f108"),
                If(bit("pflags", 0x10), [
                    emb("p1", "mgPoint_c.restore2D"),
                    emb("p2", "mgPoint_c.restore2D"),
                ], [
                    emb("p1", "mgPoint_c.restore"),
                    emb("p2", "mgPoint_c.restore"),
                ]),
            ]),
            u16("has_jet"),
            If(flag("has_jet"), [emb("jet", "gcJet_c.restore")]),
            u16("ff0"),
        ]),
    ])
    reg.define(SEG, [
        base(ENT),
        Vlt(0x4A1, [Legacy("sgSegment end points pre-0x4a1")], [
            *idx16("fc8"),
            *idx16("fcc"),
            u16("fd0"),
            u16("fd4"),
        ]),
        Vgt(0x771, [f64("seg_tol")]),
    ])
    reg.define(LINE, [
        base(SEG),
        If(lambda s, ar: (s.get("f56", 0) & 0x200) != 0, [emb("dir", "mgVector_c.restore")]),
        Vgt(0xD98, [u16("fe8")]),
    ])
    reg.define(ARC, [
        base(SEG),
        i32("fd8"),
        Vlt(0x4A1, [Legacy("sgArc pre-0x4a1")], [
            *idx16("fdc"),
            i32("fe0"),
            i32("fe4"),
            i32("fe8"),
            i32("fec"),
        ]),
    ])
    reg.define(ELLIPSE, [
        base(SEG),
        i32("fd8"),
        Vlt(0x4A1, [Legacy("sgEllipse pre-0x4a1")], [
            *idx16("fdc"),
            *idx16("fe0"),
            *idx16("fe4"),
            *idx16("fe8"),
            *idx16("fec"),
        ]),
    ])
    reg.define(PARABOLA, [
        base(SEG),
        i32("ffc"),
        i32("f100"),
        Vgt(0x13EC, [i32("f104"), i32("f108")]),
        Vgt(0xB28, [f64("fe8"), f64("ff0"), u16("ff8")]),
    ])


def spline_ops(vt1f0):
    return [
        base(SEG),
        Vge(0xF6B, [i32("f32c"), u16("f2fc")], [Legacy("sgSpline flag word pre-0xf6b")]),
        xo("f160", "suObList"),
        Vlt(0x4EB, [Legacy("sgSpline header pre-0x4eb")], [
            u16("f170"),
            u16("f0f0"),
            i32("f0f4"),
            f64("f0f8"),
            f64("f100"),
            f64("f180"),
            Vgt(0x728, [i32("f154")]),
            emb("f118", "mgVector_c.restore"),
            emb("f130", "mgVector_c.restore"),
        ]),
        Vge(0x8CD, [u16("f2f8")]),
        i32("n150"),
        Rep(signed_count("n150"), "f148", [f64("v")]),
        If(lambda s, ar: ver(ar) > 0x7F2 and (s["f32c"] & 1) == 0, [
            i32("n308"),
            Rep(signed_count("n308"), "f300", [emb("p", "mgPoint_c.restore")]),
        ]),
        Vin(0x4D2, 0x772, [u16("old_4d2")]),
        Vgt(0x80F, [
            u32("n1a8"),
            Rep("n1a8", "f1a8", [
                i32("k"),
                u16("kind"),
                emb("dir", "mgVector_c.restore"),
                If(lambda s, ar: s["kind"] == 2, [f64("mag")]),
            ]),
        ]),
        Vgt(0x8CC, [
            i32("n330"),
            If(lambda s, ar: s["n330"] != -1, [
                i32("dim"),
                f64("f80"),
                f64("f88"),
                Rep(signed_count("n330"), "params", [f64("v")]),
                Rep(signed_count("n330"), "kinds", [u16("v")]),
                Rep(signed_count("n330"), "index", [i32("v")]),
                Rep(lambda s, ar: max(s["n330"] * s["dim"], 0), "coords", [f64("v")]),
            ]),
        ]),
        Vgt(0x8E4, [i32("f314"), Vgt(0x8F5, [u16("f318"), u16("f31c")])]),
        If(lambda s, ar: s.get("f314", 0) != 0 and (s.get("n308", 0) > 0 or vt1f0), [
            u32("m330"),
            i32("dim2"),
            f64("g80"),
            f64("g88"),
            Rep(lambda s, ar: s["m330"] if s["m330"] < 0x80000000 else 0, "weights", [f64("v")]),
        ]),
        Vgt(0xD7C, [i32("f174")]),
        If(lambda s, ar: (s["f32c"] & 4) != 0, [
            cstr("f1b0"),
            cstr("f1b8"),
            Vgt(0x104F, [cstr("f1c0")]),
            cstr("f1c8"),
            cstr("f1d0"),
            cstr("f1d8"),
            i32("fixed"),
            i32("f1e0"),
            emb("f1e8", XFORM_OP),
        ]),
        Vgt(0x951, [i32("f951")]),
    ]


def define_splines(reg):
    reg.define(SPLINE, spline_ops(False))
    reg.define(SPLINE_STYLE, spline_ops(True))
    reg.define(SPLINE_8E00, [
        emb("body", "mo_loadBodyFromArchive"),
        Vge(0xAA8, [u16("fd8"), If(flag("fd8"), [f64("tol")])]),
        Vge(0xAD0, [i32("fad0")]),
    ])
    reg.define(PLANE3D, [
        base(ENT),
        emb("origin", "mgPoint_c.restore"),
        emb("xaxis", "mgVector_c.restore"),
        emb("yaxis", "mgVector_c.restore"),
        Vgt(0xB2D, [f64("f120"), f64("f128")]),
        Vgt(0xB59, [f64("f130"), f64("f138")]),
        Vgt(0xB6C, [Rep(lambda s, ar: 4, "border", [f64("v")]), u8("f180")]),
        Vgt(0xB7E, [u8("has_name"), If(flag("has_name"), [cstr("name")])]),
        Vge(0x1297, [f64("f190")]),
        Vgt(0x12B3, [u8("has_fc"), If(flag("has_fc"), [emb("face_centre", "mgPoint_c.restore")])]),
    ])
    reg.define(CONE3D, [
        base(ENT),
        emb("axis", "mgVector_c.restore"),
        emb("apex", "mgPoint_c.restore"),
        f64("ff0"),
        f64("ff8"),
        f64("f100"),
    ])


def spline_entry():
    return [
        Vlt(0x49C, [Legacy("sgSketch spline flags pre-0x49c")], [u16("flags")]),
        If(bit("flags", 1), [emb("spline", SPLINE)], [
            If(bit("flags", 4), [emb("spline", SPLINE)], [
                If(bit("flags", 0x80), [emb("spline", SPLINE_STYLE)], [
                    emb("spline", SPLINE),
                    If(lambda s, ar: (s["spline"]["f32c"] & 1) == 0, [
                        If(lambda s, ar: ver(ar) > 0xA7E and (s["flags"] & 0x20) != 0, [emb("conv", SPLINE_8E00)], [
                            If(bit("flags", 0x100), [emb("conv", SPLINE_5860)]),
                        ]),
                    ]),
                ]),
            ]),
        ]),
    ]


def define_sketch(reg):
    reg.define(CREATION, [
        i32("f08"),
        i32("f0c"),
        i32("f10"),
        i32("f14"),
        Vgt(0x1407, [i32("f18")]),
        i32("f1c"),
        Vgt(0x135, [i32("f20")]),
        Vgt(0x39A, [i32("f24")]),
        Vgt(0x42F, [i32("f28")]),
        Vgt(0x447, [i32("f2c")]),
        Vgt(0x676, [i32("f30")]),
        Vgt(0xB29, [i32("f34")]),
        Vgt(0x683, [i32("f38")]),
        Vgt(0x7D8, [i32("f40")]),
        Vge(0xDE1, [i32("f3c")]),
    ])
    reg.define(COINC, [
        *pairmap("m0"),
        *pairmap("m1"),
        *pairmap("m2"),
        Vge(0x1C54, [*pairmap("m3")]),
    ])
    reg.define(EQMAP, [
        Vge(0xD7D, [count("n"), Rep("n", "vars", [cstr("k"), f64("v")])]),
    ])
    reg.define(HDATAMGR, [
        i32("n"),
        Rep(signed_count("n"), "items", [xo("h", "sgEntHandle"), xo("d", "sgEntHandleData_c")]),
    ])
    reg.define(BLOCKMGR, [
        Vlt(0x913, [emb("ids", "su_CWordArray"), emb("blocks", "rf.suObArray")], [
            i32("n"),
            Rep(signed_count("n"), "blocks", [i32("id"), xo("b", "sgBlock")]),
            Vgt(0xA1B, [
                i32("m"),
                Rep(signed_count("m"), "map", [i32("k"), u32("a"), u32("b")]),
            ]),
            Vgt(0xA0B, [emb("f40", HDATAMGR)]),
        ]),
    ])
    reg.define(LOOPMGR, [
        i32("n"),
        Rep(signed_count("n"), "loops", [
            i32("has"),
            If(flag("has"), [
                i32("f178"),
                i32("m"),
                Rep(signed_count("m"), "curves", [i32("t"), i32("i")]),
                Vgt(0xCCC, [i32("f110"), i32("f114"), i32("f118"), i32("f11c")]),
                Vgt(0x17D8, [i32("f130"), f64("f138")]),
                Vgt(0x17E3, [xo("f140", "moDisplayDim_c")]),
            ]),
        ]),
    ])
    reg.define(SLOTMGR, [
        i32("f10"),
        i32("n"),
        Rep(signed_count("n"), "slots", [i32("k"), xo("s", "sgSlot_c")]),
    ])
    reg.define(RELMGR, [
        emb("f78", "rf.suObList"),
        emb("f40", EQMAP),
    ])
    reg.define("sgSketch", [
        *sk_list("npoints", "points", [u16("kind"), emb("point", POINT)]),
        *sk_list("nlines", "lines", [
            Vlt(0x49C, [Legacy("sgSketch line flags pre-0x49c")], [u16("flags")]),
            emb("line", LINE),
        ]),
        Vge(0x136, sk_list("ntexts", "texts", [emb("text", TEXT)])),
        Vgt(0x316, sk_list("nhatches", "hatches", [emb("hatch", HATCH)])),
        *sk_list("narcs", "arcs", [
            Vlt(0x49C, [Legacy("sgSketch arc flags pre-0x49c")], [u16("flags")]),
            emb("arc", ARC),
        ]),
        Vgt(0x47, sk_list("nellipses", "ellipses", [
            Vlt(0x49C, [Legacy("sgSketch ellipse flags pre-0x49c")], [u16("flags")]),
            emb("ellipse", ELLIPSE),
        ])),
        Vgt(0x39F, sk_list("nparabolas", "parabolas", [
            Vlt(0x49C, [Legacy("sgSketch parabola flags pre-0x49c")], [u16("flags")]),
            emb("parabola", PARABOLA),
        ])),
        *sk_list("nsplines", "splines", spline_entry()),
        Vlt(0x218, [Legacy("sgSketch units table pre-0x218")]),
        Vge(0x430, sk_list("nplanes", "planes", [emb("plane", PLANE3D)])),
        Vge(0x448, sk_list("ncylinders", "cylinders", [
            emb("ent", ENT),
            emb("axis", "mgVector_c.restore"),
            emb("origin", "mgPoint_c.restore"),
            f64("radius"),
        ])),
        Vge(0x677, sk_list("nspheres", "spheres", [
            emb("ent", ENT),
            emb("centre", "mgPoint_c.restore"),
            f64("radius"),
        ])),
        Vge(0xB2A, sk_list("ncones", "cones", [emb("cone", CONE3D)])),
        Vgt(0x683, sk_list("nparametric", "parametric", [emb("ent", ENT)])),
        emb("dims", DIMS),
        *u16_list("noffsets", "offsets", [emb("o", OFFSET)]),
        Vgt(0x40F, u16_list("nskoffsets", "sketch_offsets", [emb("o", SKOFFSET)])),
        Vgt(0x8E1, u16_list("nstyled", "styled", [emb("o", STYLED)])),
        Vgt(0x499, u16_list("nintersections", "intersections", [emb("o", INTERSECTION)])),
        u16("f12c"),
        u16("f128"),
        i32("f130"),
        Vlt(0xD3, [Legacy("sgSketch creation ids pre-0xd3")], [emb("f140", CREATION)]),
        Cnd(2, [u16("ncopy"), Rep("ncopy", "copy_map", [u32("k"), u32("a"), u32("b")])]),
        Vgt(0x220, [u16("f37c")]),
        Vgt(0x249, [u16("f188")]),
        Vge(0x1801, [u16("f18c")]),
        Vgt(0x2C1, [u16("f190")]),
        If(lambda s, ar: ver(ar) > 0x3E6 and not has_condition(ar, 2) and not has_condition(ar, 1) and not has_condition(ar, 4), [
            Vlt(0x401, [Legacy("sgSketch bodies pre-0x401")]),
            Vlt(0xA46, [xo("old_a46")]),
        ]),
        Vgt(0x800, [emb("f448", LINEVIZ)]),
        Vgt(0x904, [i32("f568"), emb("f570", "mgPoint_c.restore"), Vgt(0x909, [u32("f56c")])]),
        Vgt(0xA12, [i32("f578")]),
        Vgt(0x95E, [i32("ntools"), Rep(signed_count("ntools"), "tools", [xo("o", "moSketchToolsUserObject_c")])]),
        Vgt(0xD7C, [emb("f590", RELMGR)]),
        Vgt(0xDE0, sk_list("nblocks", "blocks", [emb("ent", ENT)])),
        If(lambda s, ar: ver(ar) >= 0x1C4F, [emb("coinc", COINC)], [
            Vgt(0x1C4A, [Legacy("sgSketch 3D coincidence map 0x1c4b-0x1c4e")]),
        ]),
        Vgt(0x2398, [xo("f5d8", "suObList")]),
        Vgt(0x2F50, u16_list("nsilhouettes", "silhouettes", [emb("o", SILHOUETTE)])),
        Vgt(0x910, [emb("f580", BLOCKMGR)]),
        Vgt(0xC52, [emb("f598", LOOPMGR)]),
        Vgt(0xF25, [emb("f588", SLOTMGR)]),
        Vgt(0x1177, [i32("f134")]),
        Ctx("ctx874", [xo("f138", "moProfileFeature_c")]),
    ])


def define_dims(reg):
    reg.define(SGDIM, [
        base(DIMENSION),
        i32("f80"),
        u16("f90"),
        u16("f94"),
        u16("f98"),
        Vlt(0x2392, [Vge(0x15D, [u16("old_f68")])]),
        Vin(0xBAB, 0xBB0, [u16("old_bab"), If(flag("old_bab"), [emb("old_xform", "mgXform_c.restore")])]),
    ])
    reg.define(LOGDIM, [
        base(SGDIM),
        u16("fa0"),
        Vge(0x49, [u16("fa4")]),
    ])
    reg.define(LOG_G1, [
        base(LOGDIM),
        xo("h1", "sgEntHandle"),
    ])
    reg.define(LOG_G2, [
        base(LOGDIM),
        xo("h1", "sgEntHandle"),
        xo("h2", "sgEntHandle"),
        Vgt(0x3C9, [u16("ff8"), u16("ffc")]),
        Vgt(0x683, [xo("f108")]),
        Vgt(0x9F7, [u16("f100")]),
        Vgt(0xC5B, [i32("f110"), i32("f114")]),
        Vgt(0xCD0, [f64("f118"), f64("f120")]),
        Vgt(0xDCC, [xo("ext1", "sgEntHandle"), xo("ext2", "sgEntHandle"), xo("ext3", "sgEntHandle")]),
        Vgt(0xF0F, [u16("f150")]),
        Vgt(0x46CB, [i32("f154")]),
    ])
    reg.define(LOG_G3, [
        base(LOGDIM),
        xo("h1", "sgEntHandle"),
        xo("h2", "sgEntHandle"),
        xo("h3", "sgEntHandle"),
        Vgt(0xDCC, [xo("ext1", "sgEntHandle"), xo("ext2", "sgEntHandle"), xo("ext3", "sgEntHandle")]),
    ])
    reg.define(LOG_GROUP, [
        Vgt(0x46CB, [
            base(LOGDIM),
            u16("n"),
            Rep("n", "ids", [i32("v")]),
        ]),
    ])
    reg.define(DIM_7C0, [
        Vgt(0x1FF5, [u16("fa"), u16("fb"), u16("fc"), xo("h", "sgEntHandle")]),
    ])
    reg.define(DIM_9F0, [
        base(LOG_G1),
        Vgt(0x1FF5, [
            u16("g"),
            xo("e", "sgEntHandle"),
            xo("p1", "sgPointHandle"),
            xo("p2", "sgPointHandle"),
            xo("p3", "sgPointHandle"),
        ]),
    ])
    reg.define(VALDIM, [
        base(SGDIM),
        Vgt(0xBAF, [
            u16("fa0"),
            If(lambda s, ar: ver(ar) < 0xBF2 or s["fa0"] != 0, [emb("xform", XFORM_OP)]),
        ]),
    ])
    reg.define(VAL_G1, [
        base(VALDIM),
        xo("h1", "sgEntHandle"),
        Vgt(0xB3D, [xo("h2", "sgEntHandle")]),
        Vin(0xB61, 0xBB0, [emb("old_xform", XFORM_OP)]),
        Vgt(0x1850, [i32("g1"), i32("g2"), emb("dir", "mgVector_c.restore")]),
    ])
    reg.define(VAL_G2, [
        base(VALDIM),
        xo("h1", "sgEntHandle"),
        xo("h2", "sgEntHandle"),
        Vge(0xC9, [u16("f180"), u16("f184")]),
        Vgt(0x2DC, [u16("f1b8")]),
        Vgt(0x760, [u16("f1bc")]),
        Vgt(0x10A4, [xo("plane", "sg3DPlaneHandle")]),
        Vgt(0x1C27, [emb("dir", "mgVector_c.restore")]),
        Vin(0x2F7A, 0x2FA0, [u16("old_2f7a")]),
    ])
    reg.define(VAL_G3, [
        base(VALDIM),
        xo("h1", "sgEntHandle"),
        xo("h2", "sgEntHandle"),
        xo("h3", "sgEntHandle"),
        Vlt(0x2DD, [Legacy("sgValG3Dim quadrant pre-0x2dd")], [u16("f1a8")]),
    ])
    reg.define(DIMS, [
        *u16_list("ng1", "val_g1", [xo("d", "sgValG1Dim")]),
        *u16_list("ng2", "val_g2", [xo("d", "sgValG2Dim")]),
        Vgt(0x271, u16_list("ng3", "val_g3", [xo("d", "sgValG3Dim")])),
        Vin(0x300, 0x30D, u16_list("narclen", "arc_len", [xo("d", "sgArcLenDist")])),
        *u16_list("noffset", "offset_dims", [xo("d", "sgOffsetDim")]),
        *u16_list("nlog1", "log_g1", [emb("d", LOG_G1)]),
        *u16_list("nlog2", "log_g2", [emb("d", LOG_G2)]),
        *u16_list("nlog3", "log_g3", [emb("d", LOG_G3)]),
        If(lambda s, ar: ver(ar) > 0x4B0, [
            Vge(0x66A, u16_list("niso", "iso", [emb("d", ISO)])),
            *u16_list("nlinpatt", "linear_patterns", [emb("d", LIN_PATT)]),
            *u16_list("nlincon", "linear_patt_cons", [emb("d", PATT_CON)]),
            *u16_list("ncircpatt", "circular_patterns", [emb("d", CIRC_PATT)]),
            *u16_list("ncirccon", "circular_patt_cons", [emb("d", PATT_CON)]),
        ]),
        xo("f118", "suObList"),
        Vgt(0x1FF5, [
            *u16_list("n7c0", "list_7c0", [emb("d", DIM_7C0)]),
            *u16_list("n9f0", "list_9f0", [emb("d", DIM_9F0)]),
        ]),
        Vgt(0x46CB, [
            u16("ngroup"),
            If(lambda s, ar: not ar.ctx.get("DAT_4db92e80", 0), [Rep("ngroup", "groups", [emb("d", LOG_GROUP)])]),
        ]),
    ])
    for cls in VAL_G1_SCOPE:
        reg.define(cls, [base(VAL_G1)])
    for cls in VAL_G1_OTHER:
        reg.provisional(cls, [base(VAL_G1)])
    for cls in VAL_G2_SCOPE:
        reg.define(cls, [base(VAL_G2)])
    for cls in VAL_G2_OTHER:
        reg.provisional(cls, [base(VAL_G2)])
    for cls in VAL_G3_OTHER:
        reg.provisional(cls, [base(VAL_G3)])
    reg.define("sgAnglDim", [base(VAL_G2)])
    reg.define("sgOffsetDim", [base(VALDIM), u16("fa8"), u16("fac")])
    reg.provisional("sgSkOffsetDim", [base(VALDIM), u16("fa8"), u16("fac")])
    reg.provisional("sgValDim", [base(VALDIM)])


def define_refs(reg):
    reg.define(HANDLE, [
        Vlt(0x5B, [Legacy("sgEntHandle pre-0x5b")]),
        u16("idx"),
        If(lambda s, ar: ver(ar) >= 0x77E and s["idx"] == 0x777F, [i32("f18")]),
        If(lambda s, ar: ver(ar) >= 0x9F7 or 0x8E8 <= ver(ar) <= 0x997, [
            i32("f1c"),
            Vge(0x17D7, [i32("f08")]),
        ]),
    ])
    for cls in HANDLES:
        reg.define(cls, [base(HANDLE)])
        if cls != "sgEntHandle":
            PARENT.setdefault(cls, "sgEntHandle")
    reg.define("sgExtEnt_c", [
        Cnd(6, [Legacy("sgExtEnt_c condition 2/4 throw")]),
        Vgt(0x66, [
            xo("f08"),
            xo("f10"),
            Vin(0x176, 0x303, [xo("old_line")]),
        ], [Legacy("sgExtEnt_c pre-0x67")]),
        Vgt(0x214, [xo("f18", "moSkIntersectInfo_c")]),
        Vgt(0x64F, [xo("f20", "moSkIsoCurveInfo_c")]),
        Vgt(0x68D, [cstr("f28")]),
    ])
    reg.define("moCompSketchEntHandle_c", [
        Vlt(0x2D1, [Legacy("moCompSketchEntHandle_c pre-0x2d1")], [
            base("moCompFeature_c"),
            xo("f0f8", "sgEntHandle"),
            Vgt(0xA95, [u32("f100")]),
        ]),
    ])
    reg.define("moSketchChain_c", [
        emb("f08", "su_CDWordArray"),
        emb("f60", "su_CDWordArray"),
        u32("f28"),
        i32("f38"),
        i32("f50"),
        i32("f54"),
        u32("f58"),
        u32("f5c"),
        cstr("f80"),
        u16("flags"),
        If(lambda s, ar: s["flags"] >= 4, [Legacy("moSketchChain_c flags >= 4 throw")]),
        If(bit("flags", 1), [xo("f30", "sg3DPlaneHandle")]),
        If(bit("flags", 2), [xo("f40", "sgPointHandle"), xo("f48", "sgPointHandle")]),
        Vgt(0xB95, [u32("fd0")]),
        Vgt(0xC8D, [
            i32("nmap"),
            Rep(signed_count("nmap"), "end_map", [u32("k"), u32("v")]),
            xo("fc0", "contourTrimData_c"),
            xo("fc8", "contourTrimData_c"),
        ]),
        Vgt(0xDDC, [i32("f90"), i32("fa0")]),
        Vge(4000, [i32("fa4")]),
    ])
    reg.define("moSketchRegion_c", [
        Vgt(0x2398, [xo("f08", "suObList")]),
    ])
    reg.define("moOneContour_c", [
        emb("f20", "rf.suObArray"),
        Vgt(0xE0A, [i32("f18")], [Legacy("moOneContour_c pre-0xe0b")]),
        If(flag("f18"), [xo("f10", "moProfileFeature_c")]),
        i32("f60"),
        i32("f64"),
        Vgt(0xDDC, [i32("f68"), i32("f78")]),
        Vge(4000, [i32("f7c")]),
    ])
    reg.define("moContourChooser_c", [
        emb("f08", "rf.suObArray"),
        Vgt(0xE0A, [i32("f48")], [Legacy("moContourChooser_c pre-0xe0b")]),
        If(flag("f48"), [xo("f40", "moProfileFeature_c")]),
        Vlt(0xB7D, [Legacy("moContourChooser_c pre-0xb7d")], [
            i32("f38"),
            Vgt(0xB9B, [i32("f3c")]),
            u16("flags"),
            If(lambda s, ar: s["flags"] > 3, [Legacy("moContourChooser_c flags > 3 throw")]),
            If(bit("flags", 1), [xo("f28", "suObArray")]),
            If(bit("flags", 2), [xo("f30", "suObArray")]),
        ]),
        Vgt(0x810, [i32("f58")]),
    ])


def define(reg):
    define_helpers(reg)
    define_entities(reg)
    define_splines(reg)
    define_sketch(reg)
    define_dims(reg)
    define_refs(reg)
