from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, i32, u32, u16, i16, u8, u64, f32, f64, obj, cstr, emb, base
from Schema import If, Op, Rep, run_load, run_store

LAYER_COND = 0x40000000
CF = "utCharFormat_c"
LW0 = "utLineWidth_c.Serialize0"
ADH = "moAnnotationDataHelper_c"


class Shadow(Op):
    def __init__(self, kind, field, tag):
        self.kind, self.field, self.tag = kind, field, tag

    def load(self, ar, scope, o):
        scope[f"{self.field}#{self.tag}"] = ar.prim(self.kind)

    def store(self, ar, scope, o):
        ar.prim(self.kind, scope[self.field])


def has_cond(ar, mask):
    return (ar.ctx.get("conditions", 0) & mask) != 0


def layer(short, field):
    return If(lambda s, ar: has_cond(ar, LAYER_COND) and s[short] != -1, [obj(field)])


def ints(*offs):
    return [i32(f"f{k:x}") for k in offs]


def bytes_(*offs):
    return [u8(f"f{k:x}") for k in offs]


def dbls(*offs):
    return [f64(f"f{k:x}") for k in offs]


def define_formats(reg):
    reg.provisional(CF, [
        cstr("f08"),
        f64("f10"),
        Vgt(0xB8, [i32("f18")]),
        f64("f20"),
        u32("f30"),
        Vge(0x174, [f64("f28")]),
        Vgt(0x3EB, [f64("f38"), f64("f40"), f64("f48")]),
        Vgt(0x724, [f64("f50")]),
        Vgt(0x3EEC, [u32("f58")]),
    ])
    reg.provisional(LW0, [Vge(0xF41, [i16("f06"), f32("f00")])])
    reg.provisional("utLineWidthPrintData_c", [f32(f"f{8 + 4 * k:x}") for k in range(8)])


def define_annotations(reg):
    reg.provisional("moBaseAnnotationDefs_c", [
        *ints(0x08), f64("f10"), *ints(0x18, 0x1C, 0x20, 0x24, 0x34, 0x40),
        Vlt(0xFA8, [i32("old_fa8")]),
        i16("f44"),
        layer("f44", "f48"),
        Vgt(0x1825, [Vlt(0x1829, [u32("old_1829")])]),
        emb("f2c", LW0),
        emb("f38", LW0),
        emb("f50", CF),
        Vgt(0x1C24, [i32("f28")]),
    ])
    B = base("moBaseAnnotationDefs_c")
    reg.provisional("moRevCloudDefs_c", [B, f64("f58")])
    reg.provisional("moWeldDefs_c", [B, i32("f58"), Vgt(0x1FCB, [emb("f60", CF)])])
    reg.provisional("moSFDefs_c", [B, *ints(0x58, 0x5C), *dbls(0x60, 0x68)])
    reg.provisional("moBendNoteDefs_c", [B, *ints(0x58, 0x5C, 0x60), f64("f68")])
    reg.provisional("moGtolDefs_c", [
        B,
        Vge(0x3738, [i32("f58")]),
        Vge(0x3B05, [i32("f5c")]),
        Vgt(0x3EF3, [u16("f60")]),
    ])
    reg.provisional("moDatumDefs_c", [B, *ints(0x58, 0x68, 0x6C, 0x60, 0x64, 0x5C)])
    reg.provisional("moBalloonDefs_c", [
        B,
        *ints(0x58, 0x5C, 0x60, 0x64, 0x68, 0x6C),
        cstr("f70"), cstr("f78"), u32("f80"),
        Vgt(0x1052, [f64("f90"), f64("f88")]),
        Vgt(0x107E, [i32("fb4"), i32("fb8"), cstr("fc0")]),
        Vgt(0x1450, [f64("f98"), f64("fa0")]),
        Vge(0x181E, [f64("fa8")]),
        Vgt(0x1857, [i32("fb0")]),
    ])
    reg.provisional("moViewLocationLabelDefs_c", [
        B,
        *ints(0x58, 0x5C, 0x60),
        Vge(0x1C0D, [i32("f64"), f64("f68"), i32("f70"), Vgt(0x1C11, [f64("f78")])], [f64("f78")]),
        Vgt(0x2393, [i32("f74")]),
    ])
    reg.provisional("moNoteDefs_c", [
        B,
        *ints(0x58, 0x5C, 0x60),
        Vgt(0x1052, [f64("f68")]),
        Vgt(0x1469, [f64("f70")]),
        Vge(0x1BCA, [f64("f78")]),
        Vgt(0x2005, [i32("f80")]),
    ])
    reg.provisional("moAnnotationDefs_c", [
        i32("f10"), f64("f08"), *ints(0x14, 0x1C, 0x20, 0x24),
        Vgt(0xFA7, [i32("f28"), u32("f38")]),
        Vge(0x181D, [i32("f2c"), i32("f30")]),
        Vge(0x2F70, [i32("f18")]),
        Vge(0x376A, [i32("f34")]),
        emb("f2c0", "moBalloonDefs_c"),
        emb("f418", "moNoteDefs_c"),
        emb("f250", "moDatumDefs_c"),
        emb("f1e8", "moGtolDefs_c"),
        emb("f108", "moSFDefs_c"),
        emb("fa0", "moWeldDefs_c"),
        Vge(0x13FD, [emb("f178", "moBendNoteDefs_c")]),
        Vgt(0xF92, [emb("f4a0", "moBaseAnnotationDefs_c")]),
        Vgt(0x13FB, [emb("f40", "moRevCloudDefs_c")]),
        Vgt(0x1C06, [emb("f398", "moViewLocationLabelDefs_c")]),
    ])


def define_dims(reg):
    reg.provisional("moBaseDimDef_c", [
        i32("f08"),
        Vlt(0xF90, [i32("old_f90a")]),
        *ints(0x0C, 0x10), *dbls(0x18, 0x20), i32("f28"), *dbls(0x30, 0x38), *ints(0x40, 0x44),
        cstr("f48"), cstr("f50"), *dbls(0x58, 0x60), *ints(0x68, 0x6C, 0x70, 0x74),
        Vlt(0xF90, [i32("old_f90b"), f64("old_f90c")]),
        *ints(0x80, 0x84, 0x88, 0x8C), i16("f90"), *ints(0x94, 0x98), u32("fe0"),
        layer("f90", "fa0"),
        emb("ff0", "moLengthUserUnits_c"),
        emb("ff8", "moAngleUserUnits_c"),
        emb("fe8", CF),
        emb("fd0", "uiLFConfig_c"),
        Vge(0x1826, [emb("fd8", "uiLFConfig_c")]),
        Vgt(0x1825, [Vlt(0x1829, [u32("old_1829")]), i32("fc0")]),
        Vgt(0x1BD1, [i32("f78")]),
        Vgt(0x1BD6, [i32("f9c")]),
    ])
    B = base("moBaseDimDef_c")
    reg.provisional("moLinearDimDef_c", [
        B,
        Vgt(0x1106, [u32("f108")]),
        Vge(0x1FA6, [Vge(0x2F8B, [i32("f100")], [i32("old_f100")])]),
        Vgt(0x3EF8, [i32("f104")]),
    ])
    reg.provisional("moAngleDimDef_c", [B, Vgt(0x27A5, [u32("f100")])])
    reg.provisional("moArcLengthDimDef_c", [B])
    reg.provisional("moRadialDimDef_c", [B, u32("f100"), Vgt(0x143F, [i32("f104")])])
    reg.provisional("moHoleCalloutDimDef_c", [B, Vgt(0xF75, [u32("f100")])])
    reg.provisional("moOrdinateDimDef_c", [B, i32("f100"), Vgt(0xFAC, [u32("f104")]), Vgt(0x23C1, [f64("f108")])])
    reg.provisional("moAngOrdinateDimDef_c", [
        B,
        Vgt(0x144A, [i32("f100"), u32("f104"), *ints(0x108, 0x110, 0x114)]),
    ])
    reg.provisional("moChamferDimDef_c", [
        B,
        *ints(0x100, 0x104),
        Vgt(0xF68, [*ints(0x108, 0x10C), *dbls(0x118, 0x120), *ints(0x110, 0x128)]),
    ])
    reg.provisional("moDiameterDimDef_c", [B, i32("f100"), Vgt(0xF75, [u32("f104")])])
    reg.provisional("moDimDefs_c", [
        i32("f68"),
        *dbls(*range(0x08, 0x60, 8)),
        *ints(0x60, 0x64, 0x6C, 0x70, 0x74),
        *dbls(0x78, 0x80),
        *ints(0x88, 0x8C),
        *dbls(0x90, 0x98, 0xA0),
        u32("fd8"),
        Vgt(0xF8F, [i32("fa8"), f64("fb0"), i32("fb8")]),
        Vgt(0x1041, [i32("fbc")]),
        Vgt(0x140E, [i32("fc0")]),
        Vgt(0x1BDC, [i32("fc4")]),
        Vgt(0x375D, [i32("fd0"), i32("fd4")]),
        Vge(0x3EEF, [i32("fcc")]),
        emb("fe0", "moLinearDimDef_c"),
        emb("f1f0", "moAngleDimDef_c"),
        emb("f2f8", "moArcLengthDimDef_c"),
        emb("f3f8", "moRadialDimDef_c"),
        emb("f500", "moHoleCalloutDimDef_c"),
        emb("f608", "moOrdinateDimDef_c"),
        emb("f830", "moChamferDimDef_c"),
        emb("f960", "moDiameterDimDef_c"),
        Vgt(0x144A, [emb("f718", "moAngOrdinateDimDef_c")]),
        emb("fa68", "moBaseDimDef_c"),
    ])


def define_labels(reg):
    reg.provisional("moDrViewLabelData_c", [
        *ints(0x08, 0x0C, 0x18, 0x14, 0x1C, 0x20),
        Vgt(0xCD3, [i32("f24")]),
        Vgt(0x1C14, [i32("f28")]),
        Vgt(0xF5B, [*ints(0x44, 0x2C, 0x38), i16("f48"), layer("f48", "f50")]),
        Vgt(0x13F9, [cstr("f88"), cstr("f90")]),
        Vgt(0x1802, [Vlt(0x180F, [i32("old_180f")])]),
        Vgt(0x180E, [u32("f5c")]),
        Vgt(0x1812, [i32("f10"), i32("f58")]),
        Vgt(0xF5B, [emb("f98", CF), emb("fa0", CF), emb("f30", LW0), emb("f3c", LW0)]),
        Vge(0x12C8, [emb("fa8", CF), emb("fb0", CF), emb("fb8", CF)]),
        Vge(0x1803, [emb("fc0", CF)]),
    ])
    B = base("moDrViewLabelData_c")
    reg.provisional("moDetailLabelData_c", [B, Vgt(0x3B02, [u32("fcc"), i32("fc8")])])
    reg.provisional("moSectionLabelData_c", [
        B,
        *dbls(0xC8, 0xD0, 0xD8), *ints(0xE0, 0xE4),
        Vgt(0x12D6, [i32("fec")]),
        Vgt(0x13F7, [i32("ff0")]),
        Vgt(0x1402, [i32("fe8")]),
    ])
    reg.provisional("moAuxLabelData_c", [B, Vgt(0x1817, [i32("fc8")])])
    for c in ("moOrthoLabelData_c", "moMiscLabelData_c"):
        reg.provisional(c, [B, i32("fc8"), Vgt(0x1817, [i32("fcc")])])
    reg.provisional("moLabelDefs_c", [
        *ints(0x08, 0x0C),
        emb("f18", "moDetailLabelData_c"),
        emb("fe8", "moSectionLabelData_c"),
        emb("f1e8", "moAuxLabelData_c"),
        Vgt(0xF92, [emb("f458", CF)]),
        Vgt(0x11CE, [emb("f2b8", "moOrthoLabelData_c")]),
        Vgt(0x1FC5, [emb("f388", "moMiscLabelData_c")]),
    ])


def define_tables(reg):
    reg.provisional("moGeneralTableDefs_c", [
        *ints(0x2C, 0x28), u32("f08"), i16("f0c"),
        layer("f0c", "f30"),
        Vgt(0x1180, [i32("f38")]),
        emb("f18", LW0),
        emb("f20", LW0),
        emb("f10", CF),
    ])
    B = base("moGeneralTableDefs_c")
    reg.provisional("moRevisionTableDefs_c", [B, *ints(0x40, 0x44, 0x48), u32("f58"), Vgt(0x2782, [i32("f4c"), cstr("f50")])])
    reg.provisional("moBOMTableDefs_c", [B, u32("f40"), Vgt(0x2B81, [cstr("f48"), cstr("f50"), cstr("f58")])])
    reg.provisional("moTitleBlockTableDefs_c", [B])
    reg.provisional("moHoleTableDefs_c", [
        B,
        *ints(0x40, 0x44), *dbls(0x48, 0x50), *ints(0x58, 0x5C, 0x60, 0x68, 0x6C, 0x70),
        Vgt(0x1168, [i32("f74"), i32("f78")]),
        Vge(0x11EC, [i32("f64")]),
        Vgt(0x12C5, [i32("f7c")]),
    ])
    reg.provisional("moWeldTableDefs_c", [B, Vgt(0x375F, [i32("f40")])])
    reg.provisional("moBendTableDefs_c", [
        B,
        Vgt(0x129A, [i32("f40"), i32("f44")]),
        Vgt(0x12B6, [i32("f4c")]),
        Vgt(0x141F, [i32("f48")]),
    ])
    reg.provisional("moPunchTableDefs_c", [
        B,
        Vgt(0x12FE, [*ints(0x40, 0x44), *dbls(0x58, 0x60), *ints(0x48, 0x4C, 0x6C, 0x50, 0x70, 0x68)]),
    ])
    reg.provisional("moFamilyTableDefs_c", [Vgt(0x42F1, [B, u32("f40")])])
    reg.provisional("moTableDefs_c", [
        i32("f08"),
        emb("f10", "moGeneralTableDefs_c"),
        emb("f50", "moRevisionTableDefs_c"),
        emb("fb0", "moBOMTableDefs_c"),
        emb("f150", "moHoleTableDefs_c"),
        Vgt(0xF92, [emb("f328", CF)]),
        Vgt(0x1057, [emb("f110", "moTitleBlockTableDefs_c")]),
        Vgt(0x11B8, [emb("f1d0", "moWeldTableDefs_c")]),
        Vgt(0x129A, [emb("f218", "moBendTableDefs_c")]),
        Vgt(0x130B, [emb("f268", "moPunchTableDefs_c")]),
        Vgt(0x42F1, [emb("f2e0", "moFamilyTableDefs_c")]),
        Vgt(0x1457, [f64("f330"), f64("f338")]),
    ])


def define_gtol(reg):
    reg.provisional("moGtolDatumRef.FUN_3c85e030", [
        cstr("f00"), u32("f08"), f64("f10"),
        Vge(0x334B, [cstr("f18")]),
        Vgt(0x3B0E, [Vlt(0x3B1A, [f64("old_a"), cstr("old_b"), f64("old_c"), cstr("old_d"), f64("old_e"), cstr("old_f")])]),
    ])
    reg.provisional("moGtolDatumList.FUN_3c85de90", [
        Vgt(0x373C, [u32("f18")]),
        i32("n"),
        Rep(lambda s, ar: max(s["n"], 0), "items", [emb("e", "moGtolDatumRef.FUN_3c85e030")]),
    ])
    reg.provisional("moGtolDatumCompartment.FUN_3c85e1b0", [
        i32("kind"),
        If(lambda s, ar: s["kind"] != 0,
           [emb("f08", "moGtolDatumRef.FUN_3c85e030")],
           [emb("f28", "moGtolDatumList.FUN_3c85de90")]),
    ])
    reg.provisional("moGtolItemDatum2022_c", [
        i32("kind"),
        Vgt(0x373C, [u32("f40")]),
        If(lambda s, ar: s["kind"] == 0,
           [i32("n"), Rep(lambda s, ar: max(s["n"], 0), "f28", [emb("e", "moGtolDatumCompartment.FUN_3c85e1b0")])],
           [emb("f08", "moGtolDatumRef.FUN_3c85e030")]),
        Vgt(0x3B19, [f64("f48"), cstr("f50"), f64("f58"), cstr("f60"), f64("f68"), cstr("f70")]),
    ])
    reg.provisional("moGtolItemIndicator_c", [i32("f00"), cstr("f08"), cstr("f10")])
    reg.provisional("moGtolItemTol2022_c", [
        i32("n08"),
        Rep(lambda s, ar: max(s["n08"], 0), "f08", [
            i32("a"),
            Vge(0x373F, [i32("b")]),
            f64("value"),
            Vge(0x334B, [cstr("text")]),
        ]),
        Shadow("i32", "f18", 0),
        *ints(0x18, 0x1C, 0x20, 0x24, 0x28, 0x2C, 0x30, 0x34, 0x38, 0x3C),
        Vge(0x373F, [
            i32("n40"),
            Rep(lambda s, ar: max(s["n40"], 0), "f40", [i32("a"), i32("b"), i32("c"), i32("d")]),
        ], [i32("old_mask"), i32("old_b"), i32("old_c"), i32("old_d")]),
        *ints(0x58, 0x5C, 0x60, 0x64, 0x68),
        Vlt(0x3724, [i32("old_3724")]),
        *ints(0x6C, 0x70),
        Vgt(0x3B10, [*ints(0x74, 0x78, 0x7C)]),
    ])
    reg.provisional("moGTolDlgDataTol_c", [
        cstr("f08"), *ints(0x10, 0x14, 0x18, 0x1C),
        If(lambda s, ar: s["f1c"] != 0, [emb("f20", "moGtolItemTol2022_c")]),
    ])
    reg.provisional("moGTolDlgDataFrame_c", [
        cstr("f08"), u8("f28"), cstr("f30"), cstr("f38"), u8("f40"), cstr("f48"), cstr("f50"),
        Vge(0xAE3, [emb(f"f{k:x}", "su_CStringArray") for k in (0x58, 0x80, 0xA8, 0xD0, 0xF8, 0x120)],
            [cstr(f"old_f{k:x}") for k in (0x58, 0x80, 0xA8, 0xD0, 0xF8, 0x120)]),
        Vgt(0x186A, [i32("f20"), i32("f24")]),
        Vge(0x3715, [
            u16("f148"), obj("f10"), obj("f18"),
            If(lambda s, ar: s["f148"] != 0, [
                emb("f150", "moGtolItemDatum2022_c"),
                emb("f1c8", "moGtolItemDatum2022_c"),
                emb("f240", "moGtolItemDatum2022_c"),
            ]),
        ]),
        Vgt(0x3718, [
            i32("n2b8"),
            Rep(lambda s, ar: max(s["n2b8"], 0), "f2b8", [emb("e", "moGtolItemIndicator_c")]),
        ]),
    ])


def define_helpers(reg):
    reg.provisional(ADH, [
        *ints(0x68, 0x6C, 0x70, 0x74), u8("f78"),
        emb("f08", CF),
        Vgt(0xF3D, [u8("f7c"), i32("f80"), f64("f88"), i32("f90"), u8("f94"), i32("f98"), f64("fa0"), i32("fa8")]),
    ])
    reg.provisional("moCenterMarkSymDataHelper_c", [
        u8("f08"), f64("f10"), u8("f18"), f64("f20"), *bytes_(0x28, 0x30, 0x34, 0x38, 0x3C, 0x2C),
        Vgt(0xF13, [emb("f80", ADH)]),
        Vgt(0xF7A, [u32("f148")]),
        Vgt(0xFA8, [*bytes_(0x40, 0x44, 0x48)]),
        Vgt(0xFAB, [u8("f4c")]),
        Vgt(0x1FD6, [f64("f78")]),
    ])
    reg.provisional("moDatumFeatureDataHelper_c", [
        *bytes_(0x08, 0x0C, 0x10), *ints(0x20, 0x24), cstr("f18"),
        Vgt(0xF4D, [cstr("f28"), *ints(0x30, 0x34, 0x38)]),
        Vgt(0xF13, [emb("f40", ADH)]),
    ])
    reg.provisional("moDatumTargetDataHelper_c", [
        cstr("f18"), cstr("f20"), cstr("f28"), cstr("f08"), cstr("f10"),
        *ints(0x30, 0x40), *dbls(0x50, 0x58), i32("f44"), *bytes_(0x34, 0x3C, 0x38, 0x48, 0x4C),
        Vgt(0x27C7, [i32("f60"), f64("f68"), i32("f70"), *bytes_(0x74, 0x90, 0xB0), emb("f78", "mgVector_c.restore")]),
        Vgt(0xF23, [emb("fc0", ADH)]),
    ])
    reg.provisional("moGTolDataHelper_c", [
        Vgt(0x920, [
            i32("n08"),
            Rep(lambda s, ar: max(s["n08"], 0), "f08", [emb("e", "moGTolDlgDataFrame_c")]),
        ]),
        *ints(0x30, 0x34), cstr("f38"), *bytes_(0x40, 0x4C, 0x50, 0x54), i32("f58"), u8("f68"),
        cstr("f70"), cstr("f78"),
        Vge(0x3751, [u8("f80"), cstr("f88"), cstr("f90"), u8("f98"), cstr("f60")]),
        *bytes_(0x9C, 0xAC, 0x110, 0x114),
        emb("fb0", CF),
        Vgt(0x967, [emb("f118", ADH)]),
        Vgt(0x1188, [*bytes_(0xA0, 0x44, 0x48)]),
        Vgt(0x2775, [*bytes_(0xA4, 0xA8)]),
        Vgt(0x3714, [u8("f1e0")]),
    ])
    reg.provisional("moSFDataHelper_c", [
        i32("f08"), *[cstr(f"f{k:x}") for k in (0x10, 0x20, 0x18, 0x28, 0x30, 0x38, 0x40)],
        Vgt(0x9A4, [cstr("f48"), cstr("f50"), cstr("f58")]),
        *bytes_(0x68, 0x6C, 0x70, 0x74), i32("f78"), *bytes_(0xA0, 0xA4, 0xA8, 0xAC), f64("fb0"), u8("fb8"),
        emb("fc0", CF),
        Vge(0x953, [u8("f120")]),
        Vgt(0x957, [u8("f124")]),
        Vgt(0x967, [emb("f128", ADH)]),
        Vgt(0x42E3, [i32("f7c"), f64("f80")]),
        Vgt(0x46BF, [cstr("f88"), cstr("f90"), i32("f98"), i32("f9c")]),
    ])
    reg.provisional("moNoteDataHelper_c", [
        *[cstr(f"f{k:x}") for k in (0x08, 0x18, 0x20, 0x28)],
        *bytes_(0x10, 0x30, 0x34, 0x38, 0x3C, 0x40), i32("f44"), f64("f50"), u8("f58"),
        *ints(0x5C, 0x60, 0x78, 0x7C, 0x80, 0x84, 0x88, 0x8C), *dbls(0x90, 0x98),
        *bytes_(0xA0, 0xA4, 0xA8, 0xAC, 0xB0, 0xB4, 0xB8, 0xBC, 0xC0, 0x12C, 0x130, 0x134),
        emb("fc8", CF),
        Vgt(0x181A, [i32("f240")]),
        Vgt(0x1842, [i32("f244")]),
        Vgt(0x2F4A, [
            u64("n248"),
            Rep(lambda s, ar: s["n248"] if s["n248"] < 0x80000000 else 0, "f248", [
                i32("key"),
                i32("kind"),
                If(lambda s, ar: s["kind"] in (1, 2, 4), [obj("value")]),
            ]),
        ]),
        Vge(0x953, [*bytes_(0x138, 0x13C, 0x140)]),
        Vgt(0x967, [emb("f150", ADH)]),
        Vge(0xA48, [u8("f48")]),
        Vgt(0xE20, [u8("f128")]),
        Vgt(0xFB3, [i32("f14c")]),
        Vgt(0x1055, [f64("f68")]),
        Vgt(0x107E, [i32("f218"), i32("f21c"), cstr("f220")]),
        Vgt(0x12BB, [*ints(0x230, 0x234, 0x238, 0x23C)]),
        Vgt(0x144F, [f64("f70")]),
        Vgt(0x1838, [f64("f228"), i32("f4c")]),
        Vgt(0x1BFB, [u8("f144")]),
        Vgt(0x3373, [u8("f148")]),
    ])
    reg.provisional("moWeldDataHelper_c", [
        u8("f08"),
        *[cstr(f"f{0x10 + 8 * j + 0x10 * k:x}") for j in range(2) for k in range(8)],
        cstr("f90"), *bytes_(0x98, 0x9C, 0xA0, 0xA4), cstr("fa8"), *bytes_(0xB0, 0xB4),
        *[op for j in range(2) for op in (
            i32(f"f{0xB8 + 4 * j:x}"), i32(f"f{0xC0 + 4 * j:x}"),
            u8(f"f{0xC8 + 4 * j:x}"), u8(f"f{0xD0 + 4 * j:x}"), u8(f"f{0xE0 + 4 * j:x}"))],
        i32("fd8"), u8("fdc"), u8("fe8"),
        *[cstr(f"f{0x218 + 8 * k:x}") for k in range(5)],
        *bytes_(0x240, 0x244, 0x248, 0x24C, 0x250, 0x254, 0x258),
        emb("ff0", CF),
        Vgt(0x1433, [u8("f150"), emb("f158", CF)]),
        Vgt(0x1438, [u8("f154"), emb("f1b8", CF)]),
        Vgt(0x957, [emb("f260", "moSFDataHelper_c"), emb("f268", "moSFDataHelper_c")]),
    ])


SWIFT = [
    ("d", 0x28), ("i", 0x30), ("i", 0x40), ("d", 0x48), ("i", 0x50), ("d", 0x58), ("i", 0x60), ("d", 0x68),
    ("i", 0x70), ("d", 0xB8), ("i", 0xC0), ("d", 0xE8), ("i", 0xF0), ("d", 0xC8), ("i", 0xD0), ("i", 0x100),
    ("d", 0xD8), ("i", 0xE0), ("d", 0x120), ("i", 0x118), ("i", 0x128), ("i", 0x210), ("d", 0x98), ("d", 0xA8),
    ("i", 0xA0), ("i", 0xB0), ("i", 0x108), ("d", 0x130), ("d", 0x140), ("i", 0x138), ("i", 0x148), ("i", 0x218),
    ("d", 0x150), ("d", 0x160), ("i", 0x158), ("i", 0x168), ("s", 0), ("d", 0x190), ("d", 0x1A0), ("i", 0x198),
    ("i", 0x1A8), ("i", 0x230), ("i", 0x1B8), ("i", 0x1C8), ("i", 0x238), ("s", 1), ("d", 0x170), ("d", 0x180),
    ("i", 0x178), ("i", 0x188), ("d", 0x2C0), ("d", 0x2D0), ("i", 0x2C8), ("i", 0x2D8), ("i", 0x220), ("i", 0x2E0),
    ("d", 0x2B8), ("d", 0x2B0), ("i", 0x258), ("i", 0x268), ("i", 0x278), ("i", 0x288), ("i", 0x298), ("i", 0x2A8),
    ("i", 0x390), ("i", 0x398), ("i", 0x388), ("i", 0x20C), ("i", 0x214), ("i", 0x224), ("i", 0x22C), ("i", 0x234),
    ("i", 0x38C), ("i", 0x384), ("i", 0x104), ("i", 0x21C), ("i", 0x2DC),
]


def swift_ops(spec):
    out = []
    for k, off in spec:
        if k == "s":
            out.append(Shadow("i32", "f220", off))
        elif k == "d":
            out.append(f64(f"f{off:x}"))
        else:
            out.append(i32(f"f{off:x}"))
    return out


def define_swift(reg):
    reg.provisional("moSwiftGtsOptions_c", [
        *swift_ops(SWIFT),
        Vgt(0xD87, [*dbls(0x38, 0xF8, 0x110, 0x1B0, 0x1C0), *ints(0x228, 0x394)]),
        Vgt(0xD9B, [
            *dbls(0x2E8, 0x2F8), *ints(0x2F0, 0x300, 0x304, 0x308),
            *dbls(0x310, 0x320), *ints(0x318, 0x328, 0x32C, 0x330),
            *dbls(0x338, 0x348), *ints(0x340, 0x350, 0x354, 0x358),
            *dbls(0x360, 0x370), *ints(0x368, 0x378, 0x37C, 0x380),
            Vgt(0xDCF, [i32("f10")]),
            Vgt(0xDDD, [*ints(0x3BC, 0x3C0)]),
            Vgt(0xDE7, [*ints(0x39C, 0x3A0, 0x3A4, 0x3A8, 0x3AC, 0x3B0, 0x3B4, 0x3B8)]),
            Vgt(0xDE8, [*ints(0x3C4, 0x3C8, 0x3CC, 0x3D0)]),
            Vgt(0xDFA, [*dbls(0x1D0, 0x1E0, 0x1F0, 0x200), *ints(0x1D8, 0x1E8, 0x1F8, 0x208, 0x23C, 0x244, 0x240, 0x248, 0x3D4, 0x3D8)]),
            Vgt(0xDFF, [*dbls(0x270, 0x280, 0x290, 0x2A0)]),
            Vgt(0xE35, [*ints(0x3E4, 0x3E0, 0x3FC, 0x3E8, 0x3EC, 0x3F0, 0x3F4)]),
            Vgt(0xF38, [i32("f400")]),
            Vgt(0xF3F, [*ints(0x404, 0x408, 0x40C, 0x410)]),
            Vgt(0xF60, [i32("f90")]),
            Vgt(0x1039, [i32("f20")]),
            Vgt(0x1094, [i32("f414")]),
            Vgt(0x3739, [i32("fc")]),
            Vge(0x3AFF, [i32("f3f8")]),
            Vgt(0x46B5, [i32("f418")]),
        ]),
    ])


def define_detail(reg):
    reg.provisional("moDetailDefs_c", [
        Vlt(0xF5C, [Old("moDetailDefs_c pre-0xf5c")]),
        i32("f10"), cstr("f13a0"), f64("f28"), u8("f30"), u32("f20"), i32("f24"), f64("f08"),
        *bytes_(0x3C, 0x14, 0x18, 0x1C, 0x34),
        i32("f1388"), u32("fec"), u32("ff0"), u32("ff4"), *dbls(0xF8, 0x100, 0x108),
        u32("f110"), u32("f114"), u32("f118"), *dbls(0x120, 0x128, 0x130),
        Vge(0x23EB, [i32("f138"), f64("f140"), f64("f148")], [i32("old_138")]),
        *ints(0xE8, 0x150, 0x154),
        Vge(0x1180, [*ints(0x158, 0x164)]),
        Vge(0x129C, [i32("f168")]),
        Vge(0x12B0, [*ints(0x16C, 0x170, 0x174)]),
        u8("f40"), *ints(0x138C, 0x1390, 0x1394, 0x1398),
        Vgt(0x11A6, [u8("f44"), u8("f48")]),
        Vgt(0x1406, [i16("fe0"), i16("fe2")]),
        Vgt(0x1423, [i32("f50"), i32("f4c")]),
        Vgt(0x1473, [f64("f2bc0"), i32("f2bc8")]),
        Vgt(0x17EC, [cstr("f2bd8"), i32("f2be0"), cstr("f2be8"), i32("f2bf0")]),
        Vgt(0x1C10, [*ints(0x178, 0x17C)]),
        Vgt(0x23D3, [*ints(0x1A8, 0x1AC, 0x1B0)]),
        Vgt(0x2BB3, [i32("f1b4")]),
        Vge(0x17F7, [i32("f180")]),
        Vge(0x1BC9, [*ints(0x184, 0x188)]),
        Vge(0x1BCD, [*ints(0x18C, 0x190, 0x194)]),
        Vge(0x17FF, [
            i32("n58"),
            Rep(lambda s, ar: max(s["n58"], 0), "f58", [cstr("s")]),
        ]),
        Vge(0x1FBB, [i32("f198")]),
        Vge(0x1FD8, [
            *ints(0x1A0, 0x1A4),
            Vgt(0x374E, [
                *[i32(f"f{0x228 + 0x20 * j + 4 * k:x}") for j in range(3) for k in range(8)],
                *[i32(f"f{0x288 + 0x20 * j + 4 * k:x}") for j in range(3) for k in range(8)],
            ], [Old("moDetailDefs_c 0x1fd8-0x374e grids")]),
        ]),
        Vgt(0x3B0F, [emb("fb8", "su_CStringArray")]),
        emb("f90", CF),
        emb("f13b0", "moDimDefs_c"),
        emb("f1f18", "moAnnotationDefs_c"),
        emb("f2410", "moTableDefs_c"),
        emb("f2750", "moLabelDefs_c"),
        emb("f2e8", "moSFDataHelper_c"),
        emb("f4d8", "moNoteDataHelper_c"),
        emb("f730", "moWeldDataHelper_c"),
        emb("f9a0", "moGTolDataHelper_c"),
        emb("fb88", "moCenterMarkSymDataHelper_c"),
        emb("fcd8", "moDatumFeatureDataHelper_c"),
        emb("fde0", "moDatumTargetDataHelper_c"),
        emb("ff68", "moSwiftGtsOptions_c"),
        emb("fb0", "utLineWidthPrintData_c"),
        Vgt(0x186D, [f64("f2bd0")]),
        Vgt(0x1BCD, [i32("f2bf4"), i32("f2bf8"), u8("f2bfc"), u8("f2c00")]),
        Vge(0x1BD2, [i32("f2c0c"), i32("f2c10")]),
        Vge(0x1C17, [i32("f54")]),
        Vge(0x1FAD, [i32("f2c04"), i32("f2c08")]),
        Vge(0x1FD7, [i32("f80"), f64("f88")]),
        Vgt(0x1FF6, [*dbls(0x2C18, 0x2C20, 0x2C28, 0x2C30, 0x2C38), *ints(*range(0x2C40, 0x2C60, 4))]),
        Vge(0x2011, [i32("f98"), emb("fa0", CF), emb("fa8", CF)]),
        Vge(0x23B1, [i32("f2c64")]),
        Vgt(0x23C0, [i32("f2c68")]),
        Vgt(0x23D8, [i32("f19c")]),
        Vgt(0x27A1, [
            i32("f1bc"), cstr("f1c0"), cstr("f1c8"), cstr("f1d0"), cstr("f1d8"),
            *ints(0x1E0, 0x1E4, 0x1E8, 0x1F8), cstr("f1f0"),
        ]),
        Vgt(0x27D1, [i32("f1fc")]),
        Vgt(0x2BB5, [*ints(0x15C, 0x160)]),
        Vgt(0x335E, [i32("f218"), cstr("f200"), cstr("f208"), cstr("f210")]),
        Vgt(0x373F, [*ints(0x220, 0x224)]),
        Vge(0x3B15, [i32("f2c6c")]),
        Vgt(0x41A1, [i32("f21c")]),
        Vgt(0x42E5, [i32("f1b8")]),
    ])


class Old(Op):
    def __init__(self, what):
        self.what = what

    def load(self, ar, scope, o):
        from Core import ArchiveError
        raise ArchiveError(f"pre-2026 path {self.what} at {ar.p}")

    def store(self, ar, scope, o):
        from Core import ArchiveError
        raise ArchiveError(f"pre-2026 path {self.what}")


def define(reg):
    define_formats(reg)
    define_annotations(reg)
    define_dims(reg)
    define_labels(reg)
    define_tables(reg)
    define_gtol(reg)
    define_helpers(reg)
    define_swift(reg)
    define_detail(reg)
