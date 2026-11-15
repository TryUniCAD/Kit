from __future__ import annotations

from Core import ArchiveError
from Dsl import base, cstr, emb, f64, i32, obj, u16, u32, u8, ver
from Schema import If, Op, Scope, run_load, run_store
from defs.ConfigPart import Cond, NCond, Norm, Present, Section
from defs.ResolvedCore import CONCEPT_LW, FEATURE_XML, concept_vt, node_vt, vt, xo


class Version2026(Op):
    def check(self, ar):
        if ver(ar) != 19000:
            raise ArchiveError(f"assembly schema requires version 19000, got {ver(ar)}")

    def load(self, ar, scope, o):
        self.check(ar)

    def store(self, ar, scope, o):
        self.check(ar)


class Unknown(Op):
    def __init__(self, field):
        self.field = field

    def load(self, ar, scope, o):
        raise ArchiveError(f"unmodelled assembly field {self.field} at {ar.p}")

    def store(self, ar, scope, o):
        raise ArchiveError(f"unmodelled assembly field {self.field} at {len(ar.out)}")


class Counted(Op):
    def __init__(self, kind, name, body):
        self.kind, self.name, self.body = kind, name, list(body)

    def read_count(self, ar):
        if self.kind == "hi-lo":
            return ar.prim("u32") << 32 | ar.prim("u32")
        return ar.prim(self.kind)

    def write_count(self, ar, value):
        if self.kind == "hi-lo":
            ar.prim("u32", value >> 32)
            ar.prim("u32", value & 0xFFFFFFFF)
        else:
            ar.prim(self.kind, value)

    def load(self, ar, scope, o):
        value = self.read_count(ar)
        if max(value, 0) > 10_000_000:
            raise ArchiveError(f"implausible assembly count {value} for {self.name}")
        scope[self.name + "#count"] = value
        items = []
        for index in range(max(value, 0)):
            item = Scope(scope, index)
            run_load(self.body, ar, item, o)
            items.append(item.own)
        scope[self.name] = items

    def store(self, ar, scope, o):
        items = scope[self.name]
        wire = scope.get(self.name + "#count", len(items))
        value = wire if max(wire, 0) == len(items) else len(items)
        self.write_count(ar, value)
        for index, fields in enumerate(items):
            run_store(self.body, ar, Scope(scope, index, fields), o)


class WithCondition(Op):
    def __init__(self, mask, body):
        self.mask, self.body = mask, list(body)

    def load(self, ar, scope, o):
        ar.ctx["conditions"] = ar.ctx.get("conditions", 0) | self.mask
        try:
            run_load(self.body, ar, scope, o)
        finally:
            ar.ctx["conditions"] = ar.ctx.get("conditions", 0) & ~self.mask

    def store(self, ar, scope, o):
        ar.ctx["conditions"] = ar.ctx.get("conditions", 0) | self.mask
        try:
            run_store(self.body, ar, scope, o)
        finally:
            ar.ctx["conditions"] = ar.ctx.get("conditions", 0) & ~self.mask


class ReadContext(Op):
    def __init__(self, key, body):
        self.key, self.body = key, list(body)

    def load(self, ar, scope, o):
        ar.ctx[self.key] = 1
        try:
            run_load(self.body, ar, scope, o)
        finally:
            ar.ctx[self.key] = 0

    def store(self, ar, scope, o):
        run_store(self.body, ar, scope, o)


def optional(kind, name, cls):
    return Present(kind, "has_" + name, name, [emb(name, cls)])


def define_root(reg):
    vt(0x4B8, "moAssembly_c", "moAssembly_c.SerializeLWData")
    vt(0x4C0, "moAssembly_c", "moAssembly_c.SerializeResolvedData")
    vt(0x3E8, "moAssembly_c", None)
    vt(0x3F8, "moAssembly_c", False)
    reg.define("moAssembly_c.SerializeLWData", [
        Section(1, [
            base("moModel_c.FUN_4c22ec80"),
            optional("u8", "f1a18", "mgBBox_c.restore"),
            optional("u8", "f1a20", "mgBBox_c.restore"),
            emb("f14a0", "su_CMapStringToString"),
            emb("f14d8", "su_CMapStringToString"),
        ]),
    ])
    reg.define("moAssembly_c.SerializeResolvedData", [
        Section(2, [
            base("moModel_c.FUN_4c234150"),
            i32("f1560"), u16("f1570"),
            obj("f15a0"), obj("f1608"), obj("f1748"), obj("f1740"),
            i32("f1750"), i32("f1598"), obj("f1590"), obj("f1868"),
            i32("f1a28"),
            emb("f18c8", "su_CObArray"),
            emb("f18e8", "su_CObArray"),
            i32("f1710"),
            If(lambda s, ar: s["f1710"] != 0, [
                obj("f1718"),
                Counted("u32", "f1720", [i32("k"), obj("a"), obj("b")]),
                obj("f1708"), i32("f1738"),
            ]),
            i32("f1940"),
            If(lambda s, ar: s["f1940"] != 0, [
                emb("f1948", "suObList"),
                emb("f1990", "suObList"),
            ]),
            i32("f1674"),
        ]),
    ])
    reg.define("moAssembly_c", [
        Version2026(),
        base("moAssembly_c.SerializeLWData"),
        base("moAssembly_c.SerializeResolvedData"),
        Cond(0x80, [Unknown("moDownstreamIdData_c under condition 0x80")]),
    ])


def define_config(reg):
    reg.define("moBaseConfiguration_c.SerializeXmlData", [base(FEATURE_XML)])
    for cls in ("moConfiguration_c", "moDeformConfiguration_c"):
        vt(0x4B8, cls, CONCEPT_LW)
        vt(0x4C0, cls, None)
        vt(0x3E8, cls, "moBaseConfiguration_c.SerializeXmlData")
        vt(0x3F8, cls, True)
    reg.define("moConfiguration_c", [
        Version2026(),
        base("moBaseConfiguration_c"),
        obj("fc48"), obj("fc50"),
        NCond(1, [obj("fca0"), obj("fca8")]),
        Counted("i32", "fce8", [obj("o")]),
        obj("fba8"), obj("fbb0"), i32("fbc0"), i32("fbc4"), obj("fbc8"),
        Cond(1, [Unknown("moConfiguration_c visual-state callback")]),
        obj("fce0"),
    ])
    reg.define("moDeformConfiguration_c", [base("moConfiguration_c")])
    reg.define("moConfig_c", [
        Version2026(),
        *[i32(name) for name in ("f08", "f0c", "f10", "f14", "f18", "f28", "f20", "f34", "f38", "f3c", "f40")],
        cstr("f48"), i32("f50"),
        *[i32(name) for name in ("f58", "f5c", "f60", "f64", "f68", "f6c", "f70")],
        Norm("u8", "f74", lambda value, ar: int(value != 0)),
    ])
    reg.define("moFeatherWeightChildrenCache_c", [
        emb("f08", "su_CObArray"), u32("f28"),
    ])
    reg.define("moConfigObject_c", [
        Version2026(),
        obj("f08"), obj("f10"),
        emb("f28", "moReferencedConfiguration_c"),
        obj("f40"), emb("f48", "moFeatherWeightChildrenCache_c"),
        optional("i32", "f140", "mgXform_c.restore"),
        emb("f78", "suObList"),
        i32("f18"), i32("f20"), i32("f148"),
        optional("i32", "f170", "mgXform_c.restore"),
        NCond(1, [obj("fc0"), obj("fc8")]),
        cstr("f178"), Norm("u8", "f190", lambda value, ar: int(value != 0)),
        emb("f118", "suObList"),
        WithCondition(0x200, [emb("fd0", "suObList")]),
    ])


def define_references(reg):
    concept_vt("moReference_c")
    reg.define("moReference_c", [
        Version2026(), base("moFeature_c"),
        optional("u8", "f360", "mgXform_c.restore"),
        optional("u8", "f370", "mgBBox_c.restore"),
        xo("f3b0", "moExtObject_c"),
        u16("f400"), Norm("u16", "f408", lambda value, ar: int(value != 0)),
        u32("f3e0"), emb("f3c0", "moReferencedConfiguration_c"),
        optional("u8", "discarded_xform", "mgXform_c.restore"),
        Present("u8", "has_f378", "f378", [
            Counted("i32", "f378", [optional("u8", "xform", "mgXform_c.restore")]),
        ]),
        i32("f450"), u32("f3f0"), obj("f468"), i32("f458"), obj("f548"),
        obj("f470"), i32("f4b0"), obj("f488"), i32("f4b4"), i32("f454"),
        obj("f490"), i32("f4d8"), i32("f418"), i32("f41c"), i32("f4c0"),
        i32("f4dc"), u32("f3e8"), i32("f4f0"), obj("f4f8"), i32("f550"),
        cstr("f500"), cstr("f508"), i32("f524"), i32("f530"), i32("f388"),
        u32("f55c"), u32("f3f4"), u32("f3f8"), obj("f538"),
        obj("discarded_stack"), i32("f49c"), i32("f4a0"), i32("f4a4"),
        i32("f3dc"),
        Cond(0x80, [Norm("u16", "f368", lambda value, ar: int(value != 0))]),
    ])
    for cls in ("moReferenceInternal_c", "moReferenceBrowser_c", "moReferenceModel_c"):
        concept_vt(cls)
        reg.define(cls, [base("moReference_c")])


def define_history(reg):
    for cls in ("moHistoryCompItemData_c", "moFavoriteCompItemData_c", "moSCCompItemData_c"):
        node_vt(cls)
    reg.define("moHistoryCompItemData_c", [
        Version2026(), base("moNode_c"),
        ReadContext("ctx8a0", [xo("f48", "moChainComponent_c")]),
    ])
    reg.define("moFavoriteCompItemData_c", [
        Version2026(), base("moNode_c"), xo("f48", "moChainComponent_c"),
    ])
    reg.define("moSCCompItemData_c", [
        Version2026(), base("moNode_c"),
        xo("f48", "moCompXFormWrapper_c"), xo("f68", "moSmartComponentFeature_c"),
        cstr("f58"), i32("f60"), xo("f50", "moCompXFormWrapper_c"),
    ])


def define_folders(reg):
    concept_vt("moLiveSectionFolder_c")
    reg.define("moLiveSectionFolder_c", [
        Version2026(), base("moFolder_c"),
        Norm("i32", "f378", lambda value, ar: int(value == 1)),
    ])


def define_mates(reg):
    for cls in ("moMateGroup_c", "moMateParent", "moMate", "moMateNGeoms_c", "moMate2Geoms_c", "moMateCoincident", "moMateParallel", "moMatePerpendicular", "moMateTangent", "moMateDim_c", "moMateDistanceDim_c"):
        concept_vt(cls)
    reg.define("moMateGroup_c", [
        Version2026(), base("moModelFeature_c"),
        Counted("i32", "discarded_manager_records", [Unknown("moAemManager_c persisted entry")]),
        Counted("hi-lo", "f4e8", [i32("v")]),
        Cond(0x80, [i32("f4f8")]),
    ])
    reg.define("moMateParent", [
        Version2026(), base("moModelFeature_c"),
        i32("f390"), i32("f394"), i32("f388"),
        Counted("u32", "f370", [i32("v")]),
    ])
    reg.define("moMate", [
        base("moMateParent"), u16("f3b4"), u16("f3b8"),
        optional("u8", "f3c0", "mgVector_c.restore"),
        Counted("i32", "f3c8", [i32("k"), xo("o", "moRefWrapper_c")]),
    ])
    reg.define("moMateNGeoms_c", [
        base("moMate"), obj("f430"),
        Counted("i32", "f410", [xo("o", "moRefWrapper_c")]),
        Counted("u32", "f448", [xo("o", "suObList")]),
        obj("f470"), obj("f468"), obj("f478"), u16("f438"),
        Norm("i32", "f480", lambda value, ar: int(value != 0)),
        cstr("f488"), cstr("f490"),
    ])
    reg.define("moMate2Geoms_c", [base("moMateNGeoms_c")])
    for cls in ("moMateCoincident", "moMateParallel", "moMatePerpendicular", "moMateTangent"):
        reg.define(cls, [base("moMate2Geoms_c")])
    reg.define("moMateDim_c", [
        base("moMate2Geoms_c"), xo("f4b8", "moDisplayDim_c"), u16("f4c0"),
    ])
    reg.define("moMateDistanceDim_c", [
        base("moMateDim_c"), u16("f4d8"), i32("f4dc"), i32("f4e0"), i32("f4f4"),
    ])
    reg.define("moMateEntityHelpData_c", [
        u16("f10"), f64("f18"), f64("f20"), f64("f28"),
    ])


def define_cache_nodes(reg):
    reg.define("moConfigSpecificInfo", [cstr("f08"), i32("f10")])
    reg.define("moBCMate_c", [
        base("moConfigSpecificInfo"), cstr("f18"), u32("f20"), u32("f24"),
        cstr("f28"), cstr("f30"), i32("f38"), i32("f3c"),
    ])
    reg.define("moBCConfigObjMapInfo_c", [emb("f08", "suObList")])
    reg.define("moBCConfigurationInfo_c", [
        cstr("f08"), cstr("f10"), i32("f18"), i32("f1c"), obj("f20"),
        i32("f2c"), i32("f30"), i32("f34"), i32("f38"),
    ])
    reg.define("moBCNode_c", [
        i32("f08"), i32("f0c"), i32("f10"), u32("f14"), cstr("f18"),
        u32("f20"), cstr("f28"), cstr("f30"), i32("f38"),
        emb("f48", "mgXform_c.restore"),
        emb("f40", "suObList"), emb("f50", "suObList"),
        i32("fb0"), i32("f58"), i32("f5c"), emb("f68", "suObList"),
    ])
    for cls in ("moBCAssemblyNode_c", "moBCPartNode_c"):
        reg.define(cls, [base("moBCNode_c"), emb("fb8", "suObList")])
    reg.define("moBCChildNode_c", [])
    reg.define("moAssemblyTimings_c", [i32("discarded0"), i32("discarded1"), i32("discarded2"), i32("discarded3")])
    reg.define("moAssyFilePropContainer_c", [obj("f08"), obj("f10")])
    reg.define("moBodyMassPropsCache_c", [
        i32("f08"), f64("f10"), u32("f18"),
        Norm("u8", "f1c", lambda value, ar: int(value != 0)),
        i32("f20"), cstr("f238"), emb("f28", "moMassProp_c"),
    ])
    reg.define("moAssyMassPropsCache_c", [
        f64("fc8"),
        Counted("u32", "f08", [u32("hi"), u32("lo"), emb("cache", "moBodyMassPropsCache_c")]),
    ])
    concept_vt("moExplViewManager_c")
    reg.define("moExplViewManager_c", [
        base("moFeature_c"), obj("f358"), obj("f360"), f64("f398"),
        i32("f3a0"), i32("f3a4"), emb("f368", "su_CMapWordToOb.Serialize"),
    ])


def define(reg):
    define_root(reg)
    define_config(reg)
    define_references(reg)
    define_history(reg)
    define_folders(reg)
    define_mates(reg)
    define_cache_nodes(reg)
