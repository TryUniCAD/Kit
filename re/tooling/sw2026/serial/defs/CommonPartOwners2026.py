from __future__ import annotations

from Core import ArchiveError
from Dsl import base, count, cstr, emb, f64, i32, obj, u16, ver
from Schema import Fn, Raw, Rep
from defs.ConfigDetail import SWIFT, ints, dbls, swift_ops
from defs.ConfigPart import Len, Norm, Pos
from defs.ResolvedCore import concept_vt, xo


def require_common_part_version(ar, scope, o):
    version = ver(ar)
    if version != 19000:
        raise ArchiveError(f"common-part archive owners require ordinary version 19000, got {version}")


def modern(ops):
    return [Fn(require_common_part_version, require_common_part_version), *ops]


def define(reg):
    reg.define("moCThreadRefMgr_c", modern([
        Len("i32", "n", "f18"),
        Rep(Pos("n"), "f18", [
            i32("key"),
            Len("u32", "m", "holders"),
            Rep(lambda s, ar: s["m"], "holders", [obj("o")]),
        ]),
        Norm("i32", "f1a0", lambda value, ar: int(value != 0)),
    ]))
    reg.define("moComponent_c", modern([xo("owner")]))
    concept_vt("moEnvFolder_c")
    reg.define("moEnvFolder_c", modern([base("moFolder_c")]))
    reg.define("moFeatColorTab_c", modern([
        Len("u32", "n", "items"),
        Rep(lambda s, ar: s["n"] if s["n"] < 0x80000000 else 0, "items", [
            emb("vp", "moVisualProperties_c.restore"),
            i32("v"),
        ]),
    ]))
    concept_vt("moPrtExplViewManager_c")
    reg.define("moPrtExplViewManager_c", modern([
        base("moFeature_c"),
        obj("f358"),
        obj("f360"),
        f64("f398"),
        i32("f3a0"),
        i32("f3a4"),
        emb("f368", "su_CMapWordToOb.Serialize"),
    ]))
    reg.define("moRefIdToSketchBlockListMap_c.FUN_4c9080f0", modern([
        i32("f18"),
        obj("f30"),
        Len("i32", "n70", "f68"),
        Rep(Pos("n70"), "f68", [
            i32("key"),
            Len("i32", "m", "guids"),
            Rep(Pos("m"), "guids", [Raw("g", 16)]),
        ]),
        Len("u32", "n98", "f90"),
        Rep(lambda s, ar: s["n98"] if s["n98"] < 0x80000000 else 0, "f90", [
            Raw("k", 16),
            Raw("v", 16),
            i32("i"),
            cstr("name"),
        ]),
    ]))
    concept_vt("moSketchBlockMgr_c", xml=None)
    reg.define("moSketchBlockMgr_c", modern([
        base("moFeature_c"),
        Raw("f380", 16),
        emb("blocks", "moRefIdToSketchBlockListMap_c.FUN_4c9080f0"),
    ]))
    reg.define("moSwiftGtsOptions_c", modern([
        *swift_ops(SWIFT),
        *dbls(0x38, 0xF8, 0x110, 0x1B0, 0x1C0),
        *ints(0x228, 0x394),
        *dbls(0x2E8, 0x2F8),
        *ints(0x2F0, 0x300, 0x304, 0x308),
        *dbls(0x310, 0x320),
        *ints(0x318, 0x328, 0x32C, 0x330),
        *dbls(0x338, 0x348),
        *ints(0x340, 0x350, 0x354, 0x358),
        *dbls(0x360, 0x370),
        *ints(0x368, 0x378, 0x37C, 0x380),
        i32("f10"),
        *ints(0x3BC, 0x3C0),
        *ints(0x39C, 0x3A0, 0x3A4, 0x3A8, 0x3AC, 0x3B0, 0x3B4, 0x3B8),
        *ints(0x3C4, 0x3C8, 0x3CC, 0x3D0),
        *dbls(0x1D0, 0x1E0, 0x1F0, 0x200),
        *ints(0x1D8, 0x1E8, 0x1F8, 0x208, 0x23C, 0x244, 0x240, 0x248, 0x3D4, 0x3D8),
        *dbls(0x270, 0x280, 0x290, 0x2A0),
        *ints(0x3E4, 0x3E0, 0x3FC, 0x3E8, 0x3EC, 0x3F0, 0x3F4),
        i32("f400"),
        *ints(0x404, 0x408, 0x40C, 0x410),
        i32("f90"),
        i32("f20"),
        i32("f414"),
        i32("fc"),
        i32("f3f8"),
        i32("f418"),
    ]))
    reg.define("su_CMapWordToOb.Serialize", modern([
        count("n"),
        Rep("n", "items", [u16("k"), obj("v")]),
    ]))
