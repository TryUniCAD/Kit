from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, ver, i32, u16, u8, f64, emb, base
from Schema import If, Rep
from defs.ResolvedCore import xo, obarray, concept_vt, Cnd, Legacy, PARENT, has_condition

KEEPER = "moFilletSIdKeeper_c"
FACE_KEEPER = "moFaceFilletSIdKeeper_c"
SURF_IDS = "mo_dynSurfIdArr.Serialize"
RADIUS = "radiusObject_c"
FEATURES = ("Fillet_c", "Chamfer_c", "VarFillet_c", "moDeleteBody_c", "moShell_c")


def flag(name):
    return lambda s, ar: s[name] != 0


def signed_count(name):
    return lambda s, ar: max(s[name], 0)


def ctx874(ar):
    return bool(ar.ctx.get("ctx874", 0))


def keeper_allowed(s, ar):
    return not has_condition(ar, 1) or ctx874(ar)


def fillet_lists_skipped(s, ar):
    return (not has_condition(ar, 0x20) and not has_condition(ar, 0x200000)
            and has_condition(ar, 1) and not ctx874(ar))


def chamfer_f8a0(s, ar):
    return ver(ar) >= 0xB3 or 0x9B < ver(ar) < 0xAB


def serialize_ptr(name):
    return [i32(f"has_{name}"), If(flag(f"has_{name}"), [obarray(name)])]


def ref_ptr(name, cls):
    return [i32(f"has_{name}"), If(flag(f"has_{name}"), [xo(name, cls)])]


def fillet_bodies():
    return [
        Vgt(0xC73, [i32("has_f734")]),
        If(lambda s, ar: s.get("has_f734", 1) != 0, [
            i32("f734"),
            xo("f8b8", "moCompEdge_c"),
            i32("n890"),
            Rep(signed_count("n890"), "f890", [emb("body", "mo_loadBodyFromArchive")]),
            Vgt(0xC73, [
                i32("n9b8"),
                Rep(signed_count("n9b8"), "f9b8", [xo("k", "moCompFace_c"), xo("v", "moCompEdge_c")]),
            ]),
            Vgt(0xC81, [emb("f9e8", "rf.suObList")]),
            Vgt(0xC94, [
                i32("na60"),
                Rep(signed_count("na60"), "fa60", [
                    xo("face", "moCompFace_c"),
                    i32("n"),
                    Rep(signed_count("n"), "ids", [i32("v")]),
                ]),
            ]),
            Vgt(0xCD4, [i32("fb00")]),
            Vgt(0xCF2, [i32("f8c8"), i32("f8cc"), i32("f8d0")]),
        ]),
    ]


def define(reg):
    for c in FEATURES:
        PARENT[c] = "moBodyFeature_c"
        concept_vt(c)
    for c in ("edgeRadiusObject_c", "faceRadiusObject_c", "loopRadiusObject_c", "featRadiusObject_c"):
        PARENT[c] = RADIUS
    PARENT["pointRadiusObject_c"] = "edgeRadiusObject_c"
    reg.provisional(SURF_IDS, [
        i32("n"),
        Rep(signed_count("n"), "items", [emb("id", "moEntityId_c")]),
    ])
    reg.define(KEEPER, [emb("f18", SURF_IDS), obarray("ff0")])
    reg.define(FACE_KEEPER, [emb("f18", SURF_IDS), obarray("fe0")])
    reg.define("Chamfer_c", [
        base("moBodyFeature_c"),
        If(keeper_allowed, [Vgt(0x17F, [emb("f880", KEEPER)])]),
        xo("f888", "suObList"),
        xo("f890", "suObList"),
        xo("f898", "suObList"),
        xo("f810", "moDisplayDim_c"),
        Vge(0x77, [xo("f818", "moDisplayAngularDim_c")]),
        Vgt(0x2C6, [xo("f820", "moDisplayDistanceDim_c")]),
        Vgt(0x97, [u8("f860")]),
        If(chamfer_f8a0, [u8("f8a0")]),
        Vge(0x966, [u8("f878")]),
        Vgt(0x1D7, [
            xo("f8a8", "moCompEdge_c"),
            xo("f8b0", "moCompFace_c"),
            xo("f8b8", "moCompFace_c"),
        ]),
        Vge(0x2C7, [i32("f8c0")]),
        Vgt(0x1084, [emb("f8c8", "su_CDWordArray")]),
        Vgt(0x2CF, [
            xo("f828", "moDisplayDistanceDim_c"),
            xo("f830", "moDisplayDistanceDim_c"),
            xo("f838", "moDisplayDistanceDim_c"),
            xo("f840", "moCompEdge_c"),
            xo("f848", "moCompEdge_c"),
            xo("f850", "moCompEdge_c"),
            xo("f858", "moCompVertex_c"),
        ]),
        Vge(0x767, [u8("f87c")]),
        Vge(0x11CC, ref_ptr("f808", "moRefWrapper_c")),
        Vgt(0x2396, [u8("f8f0")]),
    ])
    reg.define("Fillet_c", [
        base("moBodyFeature_c"),
        If(fillet_lists_skipped, [], [
            Cnd(0x800, [], [
                Vgt(0x17F, [emb("f820", KEEPER)]),
                Vgt(0x267, [emb("f828", FACE_KEEPER)]),
            ]),
            xo("f848", "suObList"),
            xo("f850", "suObList"),
            xo("f858", "suObList"),
            Vgt(0x70F, [xo("f860", "suObList")]),
            Vgt(0x21B, [xo("f878", "suObList")]),
            Vge(0x2DE, serialize_ptr("f8e0")),
            Vgt(0x3FF, [obarray("f8f8")]),
            Vgt(0x826, [xo("f880", "suObList")]),
        ]),
        xo("f830", "moDisplayDim_c"),
        Vgt(0x49F, [xo("f868", "suObList")]),
        Vge(0x4B0, [u8("f808")]),
        Vge(0x4D3, [xo("f870", "suObList")]),
        u8("f81c"),
        Vgt(0xC0, [i32("f8e8")]),
        Vgt(0x4DB, [u8("f930")]),
        Vgt(0x233, [xo("f888", "moPointRef_w")]),
        Vge(0x258, [
            Vlt(0x2D5, [Legacy("Fillet_c f8d4 clamp pre-0x2d5")], [u8("f8d4")]),
            Vgt(0x4CD, [u8("f8d8")]),
        ]),
        Vge(0x2E2, [u16("f8dc")]),
        Vgt(0x4D8, [i32("f940")]),
        Vgt(0x642, [u8("f934")]),
        Vgt(0x712, [i32("f918"), f64("f920"), f64("f928")]),
        Vge(0x710, [u8("f93c")]),
        Vgt(0x8D4, [u8("f944")]),
        Vgt(0xA0E, [u8("f948")]),
        Vge(0x11C8, ref_ptr("f810", "moFeatureRefWrapper_c")),
        If(keeper_allowed, [
            Vge(0xC57, [
                Vlt(0xC74, [Legacy("Fillet_c FUN_1802b4f40 environment preference 0x4f3 pre-0xc74")], fillet_bodies()),
            ]),
        ]),
        Vgt(0xDB9, [i32("fb98")]),
        Vgt(0xDCD, [
            i32("nbf0"),
            Rep(signed_count("nbf0"), "fbf0", [i32("f00"), i32("f04"), f64("f08"), xo("edge", "moCompEdge_c")]),
        ], [Legacy("Fillet_c fbf0 map pre-0xdce gated by global 0x18062852c")]),
        Vgt(0x1071, [emb("fc20", "su_CDWordArray")]),
        Vgt(0x182A, [
            xo("f838", "moDisplayDim_c"),
            xo("f840", "moDisplayDim_c"),
            u8("f94c"),
            i32("f8ec"),
        ]),
        Vge(0x2397, [i32("f8f0")]),
        Vgt(0x2B8E, [u8("fc48"), xo("fc40", "suObList")]),
    ])
    reg.define("VarFillet_c", [
        base("moBodyFeature_c"),
        Vgt(0x17F, [emb("f870", KEEPER)]),
        xo("f878", "suObList"),
        xo("f880", "suObList"),
        u8("f824"),
        u8("f814"),
        Vgt(0xC0, [i32("f818")]),
        Vge(0x50E, [xo("f888", "suObList")]),
        Vge(0x727, [xo("f830", "suObList")]),
        Vge(0xBF3, [i32("f838")]),
        Vgt(0x1084, [emb("f840", "su_CDWordArray")]),
        Vgt(0x182A, [u8("f810"), i32("f81c")]),
        Vgt(0x1BBD, [xo("f890", "suObList")]),
        Vgt(0x1FA3, [u8("f820")]),
        Vgt(0x4268, [u8("f828")]),
    ])
    reg.define("moShell_c", [
        base("moBodyFeature_c"),
        xo("f828", "suObList"),
        xo("f818", "moDisplayDim_c"),
        u8("f820"),
        Vge(0x163, [xo("f830", "suObList"), xo("f838", "suObList")]),
        Vgt(0x468, [xo("f848", "moCompEdge_c")]),
        Vgt(0x7DE, [xo("f850", "moCompSolidBody_c")]),
    ])
    reg.define("moDeleteBody_c", [
        base("moBodyFeature_c"),
        xo("f808", "moDeleteBodyData_c"),
    ])
    reg.define("moDeleteBodyData_c", [
        obarray("f08"),
        Vgt(0x1BC3, [i32("f28")]),
    ])
    reg.define(RADIUS, [xo("f08", "moDisplayDim_c")])
    reg.define("edgeRadiusObject_c", [
        base(RADIUS),
        xo("f10", "moCompEdge_c"),
        Vgt(0x4F2, [i32("f20")]),
    ])
    reg.define("faceRadiusObject_c", [base(RADIUS), xo("f10", "moCompFace_c")])
    reg.define("pointRadiusObject_c", [base("edgeRadiusObject_c"), xo("f28", "moPointRef_w")])
    reg.define("loopRadiusObject_c", [base(RADIUS), xo("f20", "moCompLoop_c"), xo("f10", "moCompEdge_c")])
    reg.define("featRadiusObject_c", [base(RADIUS), xo("f10")])
    reg.define("moEdgeDim_c", [
        xo("f10", "moCompEdge_c"),
        Vgt(0x757, [i32("f08"), i32("f0c")], [Legacy("moEdgeDim_c u8 values pre-0x758")]),
    ])
    reg.define("moVertDim_c", [
        xo("f08", "moDisplayDim_c"),
        xo("f10", "moCompVertex_c"),
        Vge(0x456, [u8("f28")]),
        Vge(0x182B, [xo("f18", "moDisplayDim_c"), xo("f20", "moDisplayDim_c")]),
    ])
    reg.define("moFaceBlendItemPair_c", [
        xo("f08", "moFaceBlendItem_c"),
        xo("f10", "moFaceBlendItem_c"),
    ])
    reg.define("moFaceBlendItem_c", [
        xo("f08", "moFaceRef_c"),
        xo("f10", "moEdgeRef_c"),
        u8("has_f18"),
        If(flag("has_f18"), [emb("f18", "mgPoint_c.restore")]),
    ])
