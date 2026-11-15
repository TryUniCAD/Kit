from __future__ import annotations

from Core import ArchiveError, Load, Obj, Store
from Dsl import Vgt, Vge, Vlt, ver, i32, u32, u16, i16, u8, f32, f64, obj, cstr, time32, rep, emb, base
from Schema import If, Fn, Raw
import Streams

STANDARDS = ("moANSI_c", "moISO_c", "moBS_c", "moDIN_c", "moJIS_c", "moGB_c", "moGOST_c")


def flag(name, default=0):
    return lambda s, ar: ar.ctx.get(name, default) != 0


def flat(s, ar):
    return ar.ctx.get("force_flat", 0) != 0


def doc_holds_model(s, ar):
    return ar.ctx.get("doc_holds_model", 0) != 0


def history_absent(s, ar):
    return ar.ctx.get("history_absent", 0) != 0


def condition(mask):
    return lambda s, ar: (ar.ctx.get("conditions", 0) & mask) != 0


def archive_version(ar):
    return ar.ctx.get("archive_version", ver(ar))


def legacy(what):
    def fail(ar, scope, o):
        raise ArchiveError(f"legacy branch {what} not modelled at {getattr(ar, 'p', '?')}")
    return Fn(fail, fail)


def Vin(lo, hi, then):
    return If(lambda s, ar: lo < ver(ar) < hi, then)


def xform_kind(s, ar, k):
    return (s["f78"] & 0xF0) == k


def define_math(reg):
    reg.provisional("mgMatrix_c.restore", [f64(f"m{k}") for k in range(9)])
    reg.provisional("mgPerspInfoBase_c.restore", [f64("f08"), f64("f10"), f64("f18"), f64("f20")])
    reg.provisional("mgPerspInfo_c.restore", [
        f64("f08"), f64("f10"), f64("f18"), f64("f20"), f64("f28"), f64("f30"),
    ])
    reg.provisional("mgMatrix5_c.restore", [i32("dim"), *[f64(f"m{k}") for k in range(25)]])
    reg.provisional("mgXform_c.restore", [
        u8("has_matrix"),
        If(lambda s, ar: s["has_matrix"] != 0, [emb("f08", "mgMatrix_c.restore")]),
        f64("f58"),
        f64("f60"),
        f64("f68"),
        f64("f70"),
        u8("f78"),
        If(lambda s, ar: xform_kind(s, ar, 0x40), [emb("f80", "mgMatrix5_c.restore")]),
        If(lambda s, ar: xform_kind(s, ar, 0x20), [emb("f80", "mgPerspInfo_c.restore")]),
        If(lambda s, ar: xform_kind(s, ar, 0x10), [emb("f80", "mgPerspInfoBase_c.restore")]),
    ])


def define_styles(reg):
    reg.define("moDimStandard_c", [
        Vlt(0x46, [
            u8("old_a"),
            Vgt(0x3C, [u8("old_b")]),
            Vge(0x44, [u8("old_c")]),
        ]),
    ])
    for c in STANDARDS:
        reg.define(c, [base("moDimStandard_c")])
    reg.define("moLineStyle_c", [
        cstr("f08"),
        cstr("f10"),
        u16("nseg"),
        rep("nseg", "f18", [f64("seg")]),
        u8("f20"),
    ])
    reg.define("utLineWidth_c.Serialize.2.0", [
        Vlt(0xF41, [i16("f06")], [i16("f06"), f32("f00")]),
    ])
    reg.define("uiLFConfig_c", [
        cstr("f08"),
        emb("f10", "utLineWidth_c.Serialize.2.0"),
        Vge(0xC9F, [i16("f18")]),
    ])
    reg.define("uiLineFontMgr_c", [
        u16("n"),
        rep("n", "f10", [cstr("key"), obj("cfg")]),
    ])
    reg.define("apLineStyleMgr_c.Load", [
        i32("n"),
        rep("n", "styles", [obj("o")]),
    ])


def define_env(reg):
    reg.define("uiSplitterInfo_c.Serialize", [
        u16("f08"), u16("f0c"), u16("f10"), u16("f14"),
        u16("f18"), u16("f1c"), u16("f20"), u16("f24"),
        rep("f08", "rows", [
            rep(lambda s, ar: s["f0c"], "cols", [
                emb("xa", "mgXform_c.restore"),
                emb("xb", "mgXform_c.restore"),
                u16("a"),
                Vgt(0x45C, [u16("b")]),
                Vgt(0x1B5, [f64("c")]),
                Vgt(0xBDA, [cstr("d")]),
            ]),
        ]),
    ])
    reg.define("uiUserModelEnv_c", [
        cstr("f08"),
        If(flag("env_splitter", 1), [emb("f10", "uiSplitterInfo_c.Serialize")]),
        Vgt(0x387, [i32("f1b0"), i32("f1b4")]),
        Vge(0x515, [emb("fe0", "uiSplitterInfo_c.Serialize")]),
        Vgt(0x8E5, [i32("f1b8"), i32("f1bc")]),
        Vgt(0xF55, [i32("f1c0")]),
        Vge(0x1FF1, [i32("f1c4")]),
    ])
    reg.define("uoJournal_c", [cstr("f08"), time32("f10"), i32("f18")])
    reg.define("moBomInfoMgr_c", [
        i32("n"),
        rep("n", "f08", [obj("o")]),
    ])


def define_members(reg):
    reg.provisional("mfcutZebraData_c", [
        f64("f08"),
        f64("f10"),
        u32("f18"),
        u32("f1c"),
        Vgt(0x75A, [i32("f20")]),
        Vgt(0x12F4, [i32("f28"), i32("f2c"), cstr("f30")]),
    ])
    reg.provisional("uoModelData_c.restore", [
        Vgt(0x99, [
            Vlt(0x17D, [legacy("uoModelData_c lights")]),
            obj("f08"),
        ]),
        Vgt(0x1BD, [i32("f10")]),
    ])
    reg.provisional("PWMaterialManager_c.restore", [
        i32("f08"),
        i32("f0c"),
        emb("list", "suObList"),
    ])
    reg.define("uoNotebookMgr_c.Serialize", [
        obj("f18"),
        emb("f10", "suObList"),
        Vgt(0xA2A, [
            i32("f28"),
            emb("f20", "suObList"),
            i32("f38"),
            emb("f30", "suObList"),
        ]),
        Vgt(0xA44, [emb("pending", "suObList")]),
    ])
    reg.define("PVDocSpecificOptionsData_c.Serialize", [
        i32("f08"), i32("f0c"), i32("f10"), i32("f2c"), i32("f18"), i32("f1c"), u32("f20"),
        Vgt(0x147E, [i32("f24"), i32("f28")]),
        Vge(0x1825, [i32("f14"), i32("f30"), i32("f34")]),
    ])
    reg.provisional("CRectNonOleItems_c", [
        obj("f08"),
        If(condition(1), [i32("f10")], [obj("f10")]),
    ])
    reg.define("uiBaseDoc_c.SerializeSWItemsOfOLEObjects", [
        u32("n"),
        rep(lambda s, ar: s["n"] if s["n"] < 0x80000000 else 0, "f7f8", [obj("o")]),
    ])
    reg.define("uiBaseDoc_c.Serialize", [
        If(lambda s, ar: flat(s, ar) or archive_version(ar) < 0x2E3, [legacy("uiBaseDoc_c::LoadPreSw98")], [
            emb("ole", "uiBaseDoc_c.SerializeSWItemsOfOLEObjects"),
            If(lambda s, ar: 0x40C <= ver(ar) < 0x429, [u32("old_40c")]),
        ]),
        Vge(0x4A4, [i32("f2a0")]),
    ])


def file_version_1000(s, ar):
    v = ver(ar)
    return v < 0xA62 or v > 0xDBB


def define_doc(reg):
    reg.define("uiModelDoc_c.Serialize", [
        Vge(0x413, [i32("fa58")]),
        Vge(0x505, [i32("fa5c")]),
        Vge(0x411, [i32("fa60"), i32("fa64")]),
        Vgt(0x10EE, [i32("fa74")]),
        If(lambda s, ar: ver(ar) < 0xDC or flat(s, ar), [emb("basedoc_early", "uiBaseDoc_c.Serialize")]),
        If(lambda s, ar: ver(ar) < 0xDC or flat(s, ar) or history_absent(s, ar), [obj("faa8")]),
        u32("clsid_a"),
        u16("clsid_b"),
        u16("clsid_c"),
        Raw("clsid_d", 8),
        If(lambda s, ar: ver(ar) < 0x3B3 or doc_holds_model(s, ar), [obj("model")]),
        obj("fac0"),
        Vgt(0x20D, [u8("fac8")]),
        emb("fae8", "mgXform_c.restore"),
        emb("faf0", "mgXform_c.restore"),
        u16("facc"),
        Vgt(0x45C, [u16("fad0")]),
        u8("fad4"),
        Vge(0x1FD, [
            i32("fad8_0"),
            Vge(0x985, [i32("fad8_1")]),
        ]),
        Vge(0x3C, [obj("fba8")]),
        Vin(0x46, 0xC0, [legacy("uiConfigurationMan_c")]),
        Vge(0xA08, [emb("f878", "apLineStyleMgr_c.Load")]),
        Vgt(0x73, [obj("f870")]),
        Vgt(0xC6, [
            u16("nenv"),
            rep("nenv", "faf8", [obj("o")]),
        ]),
        Vin(0xD7, 0x741, [legacy("headerFooter_c")]),
        If(lambda s, ar: ver(ar) > 0xDB and not flat(s, ar), [emb("basedoc", "uiBaseDoc_c.Serialize")]),
        Vgt(0xE0, [emb("fbf0", "uoModelData_c.restore")]),
        Vgt(0x70C, [obj("fb20")]),
        Vin(0x72D, 0x73D, [legacy("uiRefPlaneProps_c")]),
        If(lambda s, ar: ver(ar) < 0x3B3 or doc_holds_model(s, ar), [legacy("uiModelDoc_c vt 0x2bd0")]),
        Vin(0x740, 0x80B, [legacy("headerFooter_c list")]),
        Vin(0x770, 0xB9A, [i32("old_770")]),
        Vgt(0x77C, [i32("fb54")]),
        Vgt(0xBC3, [i32("fb3c"), i32("fb40")]),
        Vge(0x7DB, [i32("fd68")]),
        Vgt(0x872, [u8("f850")]),
        Vgt(0x8D5, [obj("fab8")]),
        Vgt(0x8E8, [u16("fb00"), u16("fb04")]),
        Vgt(0x908, [i32("fa6c")]),
        Vgt(0x90D, [obj("fa10")]),
        Vgt(0x103D, [i32("fa98")]),
        Vgt(0xA22, [emb("ffd8", "uoNotebookMgr_c.Serialize")]),
        If(file_version_1000, [Vge(0xDBC, [u32("f1000")])], [cstr("old_angle_unit")]),
        Vgt(0xA88, [u8("fa90")]),
        Vgt(0xB50, [u8("f1014")]),
        Vin(0xCB2, 0xCF8, [legacy("old expand-state maps")]),
        Vgt(0xCF7, [emb("expand_keys", "su_CStringArray"), emb("expand_vals", "su_CWordArray")]),
        Vgt(0xE5B, [u16("f7b8")]),
        Vgt(0xF1D, [
            u8("has_pwmaterial"),
            If(lambda s, ar: s["has_pwmaterial"] != 0, [emb("f1110", "PWMaterialManager_c.restore")]),
        ]),
        Vgt(0xFCF, [cstr("f1138")]),
        Vgt(0x105B, [emb("f1158", "suObList")]),
        Vgt(0x1070, [cstr("f1150")]),
        Vgt(0x108B, [emb("ff40", "suObList")]),
        Vgt(0x10B8, [cstr("f1140")]),
        Vgt(0x10D6, [emb("ff88", "su_CStringArray"), emb("ffb0", "su_CStringArray")]),
        Vgt(0x116C, [i32("f1348"), i32("f1350"), i32("f134c"), i32("f1354")]),
        Vgt(0x11B1, [i32("fa78")]),
        Vgt(0x11B3, [i32("f1358")]),
        Vgt(0x11F0, [emb("f1370", "PVDocSpecificOptionsData_c.Serialize")]),
        Vgt(0x12BF, [i32("f1388")]),
        Vgt(0x12F7, [i32("f1390")]),
        Vge(0x1304, [i32("f7bc")]),
        Vgt(0x13ED, [i32("f135c")]),
        Vgt(0x1409, [i32("f13c8"), emb("f13d0", "su_CDWordArray")]),
        Vgt(0x1420, [i32("f1400")]),
        Vge(0x1459, [i32("f1408")]),
        Vgt(0x1860, [i32("f13f0")]),
        Vgt(0x1FD3, [i32("fa7c")]),
        Vge(0x1FE3, [i32("fa80")]),
        Vgt(0x23C3, [i32("fd78")]),
        Vin(0x2F57, 0x2F64, [cstr("old_2f57")]),
        Vgt(0x2F63, [obj("f12e8")]),
        Vgt(0x2F98, [i32("f1424")]),
        Vgt(0x373D, [i32("f930")]),
        Vgt(0x3766, [i32("f1304")]),
        Vgt(0x3768, [i32("fd7c")]),
        Vgt(0x39D1, [i32("f1368")]),
        Vgt(0x3B17, [i32("f3e8")]),
        Vgt(0x46C1, [
            i32("nvar"),
            rep("nvar", "f11a0", [obj("o")]),
        ]),
    ])


DOC_CLASSES = {
    (0x83A33D30, 0x27C5, 0x11CE, bytes.fromhex("bfd400400513bb57")): "uiPartDoc_c",
    (0x83A33D36, 0x27C5, 0x11CE, bytes.fromhex("bfd400400513bb57")): "uiAssemblyDoc_c",
}


def doc_class(f):
    key = (f["clsid_a"], f["clsid_b"], f["clsid_c"], bytes(f["clsid_d"]))
    if key not in DOC_CLASSES:
        raise ArchiveError(f"unknown document CLSID {key!r}")
    return DOC_CLASSES[key]


def define_derived_docs(reg):
    reg.define("uiPartDoc_c.Serialize.own", [
        If(flag("doc_f7b4"), [], [
            Vlt(0x3B3, [legacy("uoPart_c.restore")]),
            Vge(0xA42, [f64("f1688")]),
        ]),
    ])
    reg.define("uiPartDoc_c.Serialize", [
        base("uiModelDoc_c.Serialize"),
        base("uiPartDoc_c.Serialize.own"),
    ])
    reg.provisional("uiSaveAssemblyAsPartSettings_c.Serialize", [
        i32("f08"),
        i32("f0c"),
        f64("f10"),
        i32("f18"),
        f64("f20"),
        i32("f28"),
        i32("f30"),
        i32("f34"),
        i32("f2c"),
        i32("f38"),
        i32("f3c"),
    ])
    reg.define("uiAssemblyDoc_c.Serialize.own", [
        If(flag("doc_f7b4"), [], [
            Vge(0x40B, [i32("f1840")]),
            Vge(0x934, [i32("f19c8")]),
            Vge(0x10CD, [cstr("f1a38")]),
            Vge(0x1170, [cstr("f1a40"), i32("f1a48")]),
            Vge(0x2793, [i32("f19b0"), f64("f19b8")]),
            Vge(0x3353, [i32("f19c0")]),
            Vge(0x2B6A, [emb("f1b48", "uiSaveAssemblyAsPartSettings_c.Serialize")]),
            Vge(0x3B24, [i32("f1afc")]),
        ]),
    ])
    reg.define("uiAssemblyDoc_c.Serialize", [
        base("uiModelDoc_c.Serialize"),
        base("uiAssemblyDoc_c.Serialize.own"),
    ])


def load_definition(data, reg, version=None, *, archive=None, name=None):
    ar = Load(data, 1, reg, version)
    doc = Obj("uiModelDoc_c")
    reg.run_load("uiModelDoc_c.Serialize", ar, doc.f, doc)
    doc.cls = doc_class(doc.f)
    reg.run_load(f"{doc.cls}.Serialize.own", ar, doc.f, doc)
    rest = ar.raw(ar.left())
    return Streams.StreamDoc("definition", doc, [doc], rest), ar


def store_definition(sd, reg, version=None):
    ar = Store(1, reg, version)
    reg.run_store(f"{sd.head.cls}.Serialize", ar, sd.head.f, sd.head)
    ar.raw(sd.tail)
    return bytes(ar.out)


PLANS = {
    "Contents/Definition": ("custom", (load_definition, store_definition)),
}


def define(reg):
    define_math(reg)
    define_styles(reg)
    define_env(reg)
    define_members(reg)
    define_doc(reg)
    define_derived_docs(reg)
