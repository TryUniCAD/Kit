from __future__ import annotations

from Core import ArchiveError, Obj
from Dsl import Vge, base, cstr, emb, f64, i32, obj, time32, u16, u32, u8, ver
from Schema import If, Op, Rep
from defs.ConfigAssembly import WithCondition
from defs.ConfigPart import NCond, ObjIf
from defs.ResolvedCore import Cnd, FEATURE_XML, concept_vt, vt


DRAWING_CLSID = (0x83A33D34, 0x27C5, 0x11CE, bytes.fromhex("bfd400400513bb57"))


def drawing_document(scope, ar):
    return tuple(scope[key] for key in ("clsid_a", "clsid_b", "clsid_c", "clsid_d")) == DRAWING_CLSID


class DrawingModel(Op):
    def load(self, ar, scope, o):
        if ver(ar) != 19000:
            raise ArchiveError(f"drawing Definition requires archive version 19000, got {ver(ar)}")
        ar.ctx["owner_is_drawing"] = 1
        owner = ar.obj()
        if not isinstance(owner, Obj) or owner.cls != "moDrawing_c":
            raise ArchiveError("drawing Definition CLSID disagrees with its root object")
        scope["model"] = owner

    def store(self, ar, scope, o):
        ar.ctx["owner_is_drawing"] = 1
        ar.obj(scope["model"])


class PendingDrawingField(Op):
    def __init__(self, owner):
        self.owner = owner

    def load(self, ar, scope, o):
        raise ArchiveError(f"unclassified drawing {self.owner} at {ar.p}")

    def store(self, ar, scope, o):
        raise ArchiveError(f"unclassified drawing {self.owner}")


def define_root(reg):
    lightweight = "moModel_c.FUN_4c22ec80"
    resolved = "moModel_c.FUN_4c234150"
    vt(0x4B8, "moDrawing_c", lightweight)
    vt(0x4C0, "moDrawing_c", resolved)
    reg.define("moDrawing_c", [
        base(lightweight), base(resolved),
        obj("f1430"), i32("f143c"), i32("f1444"), obj("f1458"), obj("f16a8"),
        i32("n1568"), Rep("n1568", "f1560", [
            cstr("file"), i32("n"), Rep("n", "rows", [i32("key"), obj("info"), cstr("name")]),
        ]),
        i32("n1578"), Rep("n1578", "f1570", [
            cstr("file"), i32("n"), Rep("n", "rows", [cstr("name"), i32("key"), obj("ref")]),
        ]),
        i32("n1740"), If(lambda s, ar: s["n1740"], [PendingDrawingField("root preview bucket map")]),
        emb("f14f8", "moModelNameToXmlStreamNameMap_c"),
        If(lambda s, ar: s.get("fe80") is not None, [emb("zero_instance_blocks", "rf.suObList")]),
        i32("n1538"), Rep("n1538", "f1538", [obj("o")]),
    ])
    reg.define("moModelNameToXmlStreamNameMap_c", [base("su_CMapStringToString"), i32("f38")])
    reg.define("moDrwCompPropMgr_c", [
        obj("f18"), i32("n10"), Rep("n10", "f08", [obj("model"), obj("properties")]),
    ])
    reg.define("uoSketch", [i32("profile_feature_id"), emb("f80", "mgXform_c.restore")])
    reg.define("uiDrawingDoc_c.Serialize.own", [
        u16("drawing_end_marker"), If(lambda s, ar: s["drawing_end_marker"] != 0xDAF, [PendingDrawingField("UI document trailer marker")]),
        i32("f16c8"), i32("f16dc"),
    ])


def detail_lists(*offsets):
    return [emb(f"f{offset:x}", "rf.suObList") for offset in offsets]


def define_detail_folder(reg):
    concept_vt("moDetailFolder_c", "moDetailFolder_c.SerializeXmlData")
    reg.define("moDetailFolder_c.SerializeXmlData", [
        base(FEATURE_XML),
        If(lambda s, ar: ar.ctx.get("conditions", 0) & 0x180A1, [PendingDrawingField("detail folder XML")]),
    ])
    reg.define("moDetailFolder_c", [
        base("moFeature_c"),
        *detail_lists(0x358, 0x3A0, 0x3E8, 0x430, 0x4C0, 0x550, 0x598, 0x5E0),
        *detail_lists(0x628, 0x670, 0x700, 0x748, 0x7D8, 0x820, 0x868, 0x8B0, 0x8F8, 0x478),
        emb("fd90", "mgXform_c.restore"), NCond(1, [obj("fd78")]),
        *detail_lists(0x940, 0x988, 0x9D0, 0xA18, 0xAA8, 0xAF0, 0xB38, 0x508, 0xBC8),
        *detail_lists(0x790, 0xC10, 0xC58, 0xCA0, 0xCE8),
        i32("has_fd98"), If(lambda s, ar: s["has_fd98"], [PendingDrawingField("detail folder bucket")]),
        *detail_lists(0xB80, 0xD30), i32("fde8"),
    ])


def define_sheet(reg):
    concept_vt("moDrSheet", "moDrSheet.SerializeXmlData")
    reg.define("moDrSheet.SerializeXmlData", [
        base(FEATURE_XML),
        If(lambda s, ar: ar.ctx.get("conditions", 0) & 0x180A1, [PendingDrawingField("sheet XML")]),
    ])
    reg.define("moDrSheet", [
        base("moModelFeature_c"),
        f64("f3f8"), f64("f400"), u8("f39c"), u8("f3c0"),
        f64("f3e8"), f64("f3f0"),
        ObjIf("u8", "has_f408", "f408"), ObjIf("u8", "has_f468", "f468"),
        ObjIf("u8", "has_f418", "f418"),
        u8("f3b0"), u8("f420"), u8("f428"), cstr("f3b8"), obj("f3c8"),
        NCond(0x10000000, [obj("f438")]),
        u8("has_f430"), If(lambda s, ar: s["has_f430"], [emb("f430", "mgXform_c.restore")]),
        obj("f390"), i32("f448"),
        u8("has_f450"), If(lambda s, ar: s["has_f450"], [PendingDrawingField("sheet sketch data")]),
        cstr("f3d0"), i32("f3d8"),
        u16("f368_marker"), If(lambda s, ar: s["f368_marker"] != 0xFFFF, [PendingDrawingField("sheet annotation state")]),
        i32("f474"), f64("f4a8"), f64("f4b0"), f64("f4b8"), f64("f4c0"),
        i32("f4c8"), i32("f4cc"), i32("f4d0"), i32("f4d4"), i32("f4d8"),
        i32("f4e0"), time32("f4f0"), i32("n_ink_views"), Rep("n_ink_views", "ink_views", [obj("o")]),
    ])


def define_view(reg):
    for concept in ("moDrView", "moAbsoluteView"):
        concept_vt(concept, "moDrView.SerializeXmlData")
    reg.define("moDrView.SerializeXmlData", [
        base(FEATURE_XML),
        If(lambda s, ar: ar.ctx.get("conditions", 0) & 0x180A1, [PendingDrawingField("view XML")]),
    ])
    reg.define("moDrView.Archive", [
        emb("fd28", "rf.suObArray"), base("moModelFeature_c"),
        *[emb(f"f{offset:x}", "mgXform_c.restore") for offset in (0x5E0, 0x6B8, 0x6C0)],
        *[f64(f"f{offset:x}") for offset in (0x6D8, 0x6E0, 0x6E8, 0x6F0, 0x718, 0x720, 0x728, 0x730)],
        emb("f778", "mgPoint_c.restore"), f64("f780"), f64("f788"), u8("f798"),
        If(lambda s, ar: s["f798"], [emb("f5e8", "mgXform_c.restore"), emb("f5f0", "mgXform_c.restore")]),
        u8("f79c"), cstr("fe30_name"), i32("fe30_flags"),
        u8("has_f6c8"), If(lambda s, ar: s["has_f6c8"], [obj("f6c8"), emb("f6d0", "mgVector_c.restore")]),
        ObjIf("u8", "has_f7c8", "f7c8"), ObjIf("u8", "has_f8e0", "f8e0"), ObjIf("u8", "has_fde0", "fde0"),
        obj("f5d8"), obj("f968"),
        *[u16(f"f{offset:x}") for offset in (0x7AC, 0x7BC, 0x7A8, 0x7C0, 0x7B0, 0x7B4, 0x8EC)],
        i32("f8f0"), obj("f8f8"), obj("f630"), obj("f640"), ObjIf("u16", "has_f9d8", "f9d8"),
        u16("na10"), If(lambda s, ar: s["na10"], [PendingDrawingField("view display records")]),
        *[f64(f"f{offset:x}") for offset in (0x9E8, 0x9F0, 0x9F8, 0xA00)],
        i32("f610"), i32("f614"), emb("f900", "rf.suObArray"), emb("f600", "mgBBox_c.restore"),
        u8("has_fb50"), If(lambda s, ar: s["has_fb50"], [emb("fb50", "viewSketchCache")]),
        i32("n860"), Rep("n860", "f858", [emb("vector", "mgVector_c.restore")]),
        u16("na18"), If(lambda s, ar: s["na18"], [PendingDrawingField("view detail records")]),
        f64("fb68"), i32("fb74"), emb("fb78", "rf.suObList"),
        i32("has_f648"), If(lambda s, ar: s["has_f648"], [emb("f648", "mgPoint_c.restore")]),
        obj("f658"), obj("fb58"),
        *detail_lists(0xA20, 0xA68, 0xAB0, 0xAF8),
        If(lambda s, ar: s["f610"] & 1, [f64(f"f{offset:x}") for offset in (0x878, 0x880, 0x888, 0x890)]),
        u8("f8e8"), f64("f6b0"), *detail_lists(0xC28, 0xC70), u8("fd94"), *detail_lists(0xCB8),
        i32("fe40"), i32("fdb8"), i32("f410"), f64("f3e8"), f64("f3f0"),
        u8("has_fe78"), If(lambda s, ar: s["has_fe78"], [emb("fe78", "mgPoint_c.restore")]),
        *detail_lists(0xD48), i32("fe8c"), u32("fe94"),
        i32("nf50"), Rep("nf50", "ff48", [i32("key"), obj("value")]),
        emb("ff70", "rf.su_CMapObToInt"), i32("nf68"), Rep("nf68", "ff60", [i32("key"), u32("value")]),
        *[i32(f"f{offset:x}") for offset in (0x540, 0xFA4, 0xFA8, 0xFAC, 0x618, 0xFB4, 0x558)],
        cstr("f548"), obj("f1008"), cstr("f550"),
    ])
    view = base("moDrView.Archive")
    reg.define("moDrView", [
        If(lambda s, ar: ar.ctx.get("conditions", 0) & 0x40, [view], [WithCondition(0x40, [view])]),
        Cnd(1, [i32("has_view_bodies"), If(lambda s, ar: s["has_view_bodies"], [PendingDrawingField("drawing view bodies")])]),
        emb("f608", "mgBBox_c.restore"),
        *[f64(f"f{offset:x}") for offset in (0x738, 0x740, 0x748, 0x750)],
        i32("f55c"), i32("ffbc"), i32("f590"), i32("f594"), f64("f3f8"), cstr("fff8"),
        i32("f61c"), i32("f7a0"), i32("f5a8"),
    ])
    reg.define("moAbsoluteView", [
        base("moDrView"), u16("f1010"), Vge(0xC6, [cstr("f1018"), u8("f1020")]),
        Vge(0x861, [i32("f1028")]), Vge(0x11C9, [i32("f102c")]),
        Vge(0x11D0, [i32("f1030")]),
    ])
    reg.define("moDisplayProfileFeature_c", [
        base("moDisplayObject_c.FUN_4ba4d3c0"),
        i32("n1e0"), Rep("n1e0", "f1e0", [i32("key")]), i32("f200"),
    ])
    reg.define("moDrawingRefPlnData_c", [
        base("moRefPlnData_c.serializePlaneData"), Vge(0xAB, [emb("f88", "mgXform_c.restore")]),
    ])
    reg.define("viewSketchCache", [
        i32("n"), If(lambda s, ar: s["n"], [PendingDrawingField("view sketch cache entries")]),
    ])


def define(reg):
    reg.define("moScaleSysScale_c", [])
    for folder in ("moBlockFolder_c", "moMarkupCommentFolder_c"):
        concept_vt(folder)
        reg.define(folder, [base("moFolder_c")])
    define_root(reg)
    define_detail_folder(reg)
    define_sheet(reg)
    define_view(reg)
