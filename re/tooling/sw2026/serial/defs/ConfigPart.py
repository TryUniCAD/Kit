from __future__ import annotations

from Core import ArchiveError, Load, Store, Obj
from Streams import StreamDoc, load_rooted
from Dsl import Vgt, Vge, Vlt, ver, i32, u32, u16, u8, f64, obj, cstr, emb, base, count, time32
from Schema import Op, If, Rep, Raw, Scope, run_load, run_store
from defs.ResolvedCore import CONCEPT_RES, vt, concept_vt
from defs.ConfigDetail import Shadow

NODE_LW = "moNode_c.SerializeLWData"
CONCEPT_LW = "moConcept_c.SerializeLWData"


class Old(Op):
    def __init__(self, what):
        self.what = what

    def load(self, ar, scope, o):
        raise ArchiveError(f"pre-2026 path {self.what} at {ar.p}")

    def store(self, ar, scope, o):
        raise ArchiveError(f"pre-2026 path {self.what}")


def cond(ar, mask):
    return (ar.ctx.get("conditions", 0) & mask) != 0


def Cond(mask, then, other=()):
    return If(lambda s, ar: cond(ar, mask), then, other)


def NCond(mask, then, other=()):
    return If(lambda s, ar: not cond(ar, mask), then, other)


def Nz(field, then, other=()):
    return If(lambda s, ar: s[field] != 0, then, other)


def Pos(field):
    return lambda s, ar: max(s[field], 0)


class Direct(Op):
    def load(self, ar, scope, o):
        ar.count += ar.ctx["direct"]
        ar.base = ar.count

    def store(self, ar, scope, o):
        ar.count += ar.ctx["direct"]


class Section(Op):
    def __init__(self, kind, body):
        self.kind, self.body = kind, list(body)

    def load(self, ar, scope, o):
        n = ar.prim("u32")
        start = ar.p
        run_load(self.body, ar, scope, o)
        if ar.p - start != n:
            error = ArchiveError(f"section type {self.kind} declares {n} bytes, schema read {ar.p - start} (ends at {ar.p}, expected {start + n})")
            fields = getattr(scope, "own", scope)
            error.details = {
                "fields": {key: value for key, value in fields.items() if isinstance(value, (int, float))},
                "counts": {key: len(value) for key, value in fields.items() if isinstance(value, list)},
                "section_start": start,
                "cursor": ar.p,
                "end_bytes": ar.b[max(start, start + n - 32):start + n].hex(),
            }
            raise error

    def store(self, ar, scope, o):
        at = len(ar.out)
        ar.prim("u32", 0)
        start = len(ar.out)
        run_store(self.body, ar, scope, o)
        ar.out[at:at + 4] = (len(ar.out) - start).to_bytes(4, "little")


class Present(Op):
    def __init__(self, kind, flag, field, body):
        self.kind, self.flag, self.field, self.body = kind, flag, field, list(body)

    def load(self, ar, scope, o):
        v = ar.prim(self.kind)
        scope[self.flag] = v
        if v != 0:
            run_load(self.body, ar, scope, o)

    def store(self, ar, scope, o):
        on = self.field in getattr(scope, "own", scope)
        flag = scope.get(self.flag, 1 if on else 0)
        ar.prim(self.kind, flag)
        if flag != 0:
            run_store(self.body, ar, scope, o)


class Len(Op):
    def __init__(self, kind, name, items):
        self.kind, self.name, self.items = kind, name, items

    def load(self, ar, scope, o):
        scope[self.name] = ar.prim(self.kind)
        if scope[self.name] == 0:
            scope[self.items] = []

    def store(self, ar, scope, o):
        ar.prim(self.kind, len(scope[self.items]))


class Norm(Op):
    def __init__(self, kind, name, fn):
        self.kind, self.name, self.fn = kind, name, fn

    def load(self, ar, scope, o):
        value = ar.prim(self.kind)
        scope[self.name + "#wire"] = value
        scope[self.name] = self.fn(value, ar)

    def store(self, ar, scope, o):
        value = scope[self.name]
        wire = scope.get(self.name + "#wire", value)
        ar.prim(self.kind, wire if self.fn(wire, ar) == value else value)


class ObjIf(Op):
    def __init__(self, kind, flag, field):
        self.kind, self.flag, self.field = kind, flag, field

    def load(self, ar, scope, o):
        v = ar.prim(self.kind)
        scope[self.flag] = v
        if v != 0:
            scope[self.field] = ar.obj()

    def store(self, ar, scope, o):
        v = getattr(scope, "own", scope).get(self.field)
        flag = scope.get(self.flag, 0 if v is None else 1)
        ar.prim(self.kind, flag)
        if flag != 0:
            ar.obj(scope[self.field])


class ObjShadow(Op):
    def __init__(self, field, tag):
        self.field, self.tag = field, tag

    def load(self, ar, scope, o):
        scope[f"{self.field}#{self.tag}"] = ar.obj()

    def store(self, ar, scope, o):
        key = f"{self.field}#{self.tag}"
        ar.obj(scope[key] if key in scope else scope[self.field])


class PartOnly(Op):
    def __init__(self, body):
        self.body = list(body)

    def load(self, ar, scope, o):
        if o.cls == "moPart_c":
            run_load(self.body, ar, scope, o)

    def store(self, ar, scope, o):
        if o.cls == "moPart_c":
            run_store(self.body, ar, scope, o)


class GhostCount(Op):
    def load(self, ar, scope, o):
        packed = ar.prim("i32")
        if ver(ar) > 0xFD8:
            flags = packed >> 28
            n = packed - flags * 0x10000000
        else:
            flags, n = 0, packed
        scope["fe0"] = flags
        scope["n"] = n

    def store(self, ar, scope, o):
        v = (scope["fe0"] * 0x10000000 + len(scope["objects"])) & 0xFFFFFFFF
        ar.prim("i32", v - (1 << 32) if v >= 1 << 31 else v)


class MassCaches(Op):
    def load(self, ar, scope, o):
        n = ar.prim("i32")
        if not 0 <= n <= 2:
            raise ArchiveError(f"unsupported mass cache count {n}")
        items = []
        for i in range(max(n, 0)):
            sub = Scope(scope, i)
            ar.registry.run_load("moMassPropCache_c.Serialize", ar, sub, o)
            items.append(sub.own)
        scope["f1628"] = items
        scope["f1638"] = ar.prim("i32") if n > 1 else 0

    def store(self, ar, scope, o):
        items = scope["f1628"]
        if len(items) > 2:
            raise ArchiveError(f"unsupported mass cache count {len(items)}")
        ar.prim("i32", len(items))
        for i, item in enumerate(items):
            ar.registry.run_store("moMassPropCache_c.Serialize", ar, Scope(scope, i, item), o)
        if len(items) > 1:
            ar.prim("i32", scope["f1638"])


class BBoxCache(Op):
    def load(self, ar, scope, o):
        n = ar.prim("i32")
        if not 0 <= n <= 10_000_000:
            raise ArchiveError(f"unsupported bounding box cache count {n}")
        items = []
        for _ in range(max(n, 0)):
            k = ar.prim("i32")
            items.append({"k": k, "o": ar.obj() if k > 0 else None})
        scope["f1640"] = items

    def store(self, ar, scope, o):
        items = scope["f1640"]
        ar.prim("i32", len(items))
        for e in items:
            ar.prim("i32", e["k"])
            if e["k"] > 0:
                ar.obj(e["o"])


def model_header_direct(arc, name, reg):
    data = arc.get(name + "-ModelHeader")
    if data is None:
        raise ArchiveError(f"{name}-ModelHeader missing; direct load array count unknown")
    doc, _ = load_rooted(data, reg, 1)
    hdr = next((r for r in doc.roots if isinstance(r, Obj) and r.cls == "moHeader_c"), None)
    if hdr is None:
        raise ArchiveError("moHeader_c not found in ModelHeader stream")
    k = 1 if hdr.f.get("f38") is not None else 0
    lst = hdr.f.get("f30")
    if lst is not None:
        if not isinstance(lst, Obj) or "items" not in lst.f:
            raise ArchiveError(f"moHeader_c.f30 list {lst!r} not modelled")
        k += len(lst.f["items"])
    return k


def load_config(data, reg, version=None, *, archive=None, name="Contents/Config-0"):
    if archive is None:
        raise ArchiveError(f"{name} requires its owning archive")
    k = model_header_direct(archive, name, reg)
    ar = Load(data, 1, reg, version, {"direct": k})
    root = ar.obj()
    rest = ar.raw(ar.left())
    return StreamDoc(name, {"direct": k}, [root], rest), ar


def store_config(doc, reg, version=None):
    ar = Store(1, reg, version, {"direct": doc.head["direct"]})
    for o in doc.roots:
        ar.obj(o)
    ar.raw(doc.tail)
    return bytes(ar.out)


PLANS = {"Contents/Config-0": ("custom", (load_config, store_config))}


def define(reg):
    reg.provisional("moNodeName_c", [cstr("f08")])
    reg.define("moModel_c.FUN_4c17aa00", [
        Direct(),
        Vgt(0x23D, [i32("fb0")]),
        Vgt(0x758, [u32("fb4")]),
        base(CONCEPT_LW),
    ])
    reg.define("moVizPropPropListElt_c.FUN_4c2409d0", [
        Vgt(0x90, [i32("f10"), emb("f08", "moVisualProperties_c.restore")]),
    ])
    reg.define("moVizPropFaceListElt_c.FUN_4c240810", [
        Vgt(0x90, [
            emb("f08", "moVizPropPropListElt_c.FUN_4c2409d0"),
            obj("f20"),
            Vge(0x1F7, [i32("f28")]),
        ]),
        Vgt(0x103A, [i32("f1c"), i32("f18")]),
    ])
    reg.define("moFaceVizProps_c.restore", [
        Vgt(0x90, [
            i32("n08"),
            Rep(Pos("n08"), "faces", [emb("e", "moVizPropFaceListElt_c.FUN_4c240810")]),
            i32("n58"),
            Rep(Pos("n58"), "props", [emb("e", "moVizPropPropListElt_c.FUN_4c2409d0")]),
        ]),
    ])
    reg.define("moVizBodyPropPropElt_c.FUN_4c240770", [
        Vgt(0x657, [i32("f10"), emb("f08", "moVisualProperties_c.restore")]),
    ])
    reg.define("moBodyVizProps_c.FUN_4c240300", [
        Vgt(0x657, [
            i32("n08"),
            Rep(Pos("n08"), "bodies", [
                Vgt(0x657, [
                    emb("f08", "moVizBodyPropPropElt_c.FUN_4c240770"),
                    obj("f18"),
                    i32("f20"),
                ]),
                Vgt(0x103B, [i32("f24")]),
            ]),
            i32("n58"),
            Rep(Pos("n58"), "props", [emb("e", "moVizBodyPropPropElt_c.FUN_4c240770")]),
        ]),
    ])
    reg.define("su_CMapStringToOb.Serialize", [
        count("n"),
        Rep("n", "items", [cstr("key"), obj("value")]),
    ])
    reg.define("moModel_c.FUN_4c216d80", [
        emb("f18", "su_CMapStringToOb.Serialize"),
        Vlt(0x1C2, [Old("FUN_4c216d80 lists at 0x118/0x148")]),
        Vlt(0x4B, [i32("old_4b")]),
        Vgt(0x1C1, [i32("f110"), i32("f114")]),
    ])
    reg.define("moModel_c.FUN_4c22ec20", [
        i32("kind"),
        If(lambda s, ar: s["kind"] == 2, [base("moModel_c.FUN_4c216d80")]),
    ])
    reg.define("suDynArray.FUN_4ba47010", [
        u32("size"),
        Nz("size", [
            u32("a"),
            u32("b"),
            u32("n"),
            Raw("data", lambda s, ar: s["n"] * s["size"]),
        ]),
    ])
    reg.define("moModel_c.FUN_4c22ec80", [
        base("moModel_c.FUN_4c17aa00"),
        Vge(0xF98, [obj("f9b8")], [Old("moUnitsTable_c default pre-0xf98")]),
        Vgt(0x8DD, [Vlt(0x959, [Old("moFeatureRefMgr_c 0x8de-0x958")])]),
        obj("f990"),
        emb("fdd0", "moFaceVizProps_c.restore"),
        u8("fd30"),
        obj("fa70"),
        obj("fdb0"),
        u8("has_f7f8"),
        Nz("has_f7f8", [emb("f7f8", "mgBBox_c.restore")]),
        Vgt(0xCF4, [i32("fef8")]),
        Vgt(0xCFA, [
            i32("n168"),
            Rep(Pos("n168"), "f168", [i32("key"), obj("value")]),
        ]),
        Vgt(0xD05, [i32("ff18")]),
        Vgt(0xDC0, [i32("ff20")]),
        Vgt(0xDE1, [i32("ff2c")]),
        Vgt(0xF5B, [
            i32("n180"),
            Rep(Pos("n180"), "f178", [cstr("key"), obj("value")]),
        ]),
        Vgt(0xFCA, [f64("ff80"), f64("ff88")]),
        Vgt(0x12D8, [emb("fa98", "moModel_c.FUN_4c22ec20")]),
        NCond(0x80, [Vgt(0x2777, [
            i32("f160"),
            Nz("f160", [emb("f150", "suDynArray.FUN_4ba47010")]),
        ])]),
        Vgt(0xE0F, [i32("ff1c")]),
        Vgt(0xF2E, [
            i32("shrinkwrap"),
            Vgt(0x2F72, [i32("defeatured")]),
            Nz("shrinkwrap", [Old("moShrinkWrapData_c FUN_4c0c4b80")]),
        ]),
        Vgt(0x17E6, [i32("fd50")]),
        Vgt(0x1FBE, [emb("fc90", "suObList")]),
        Vge(0x1FCE, [i32("fd58")]),
        Vgt(0x1FD6, [
            i32("ncd8"),
            Rep(Pos("ncd8"), "fcd8", [
                cstr("key"),
                i32("m"),
                Rep(Pos("m"), "notes", [obj("o")]),
            ]),
        ]),
        Vge(0x2003, [Raw("f784", 16), i32("f1188"), Raw("f7a4", 16), i32("f118c")]),
        Vge(0x2010, [i32("f1190"), i32("f1194")]),
        Vgt(0x23C9, [
            i32("has_f1180"),
            Nz("has_f1180", [Old("moComponentImportData_c FUN_4b2b2410")]),
        ]),
        Vgt(0x27CC, [i32("f280")]),
        Vgt(0x2B6C, [u32("f1300")]),
        Vgt(0x46BB, [
            i32("f1308"),
            Vgt(0x46C5, [
                i32("n1318"),
                Rep(lambda s, ar: s["n1318"] & 0xFFFFFFFF, "f1310", [u32("key"), i32("value")]),
            ]),
        ]),
        Vgt(0x2BCE, [obj("f2f8")]),
    ])
    reg.define("moModel_c.FUN_4c210610", [
        i32("n"),
        Rep(lambda s, ar: s["n"] & 0xFFFFFFFF, "items", [i32("key"), i32("value")]),
    ])
    reg.define("moPart_c.FUN_4c2309d0", [
        Section(1, [
            base("moModel_c.FUN_4c22ec80"),
            obj("f1418"),
            Vgt(0xF36, [Vlt(0xF42, [Old("gcXBodyhatchManager_c 0xf37-0xf41")])]),
            obj("f1420"),
            obj("f1588"),
            emb("f938", "moBodyVizProps_c.FUN_4c240300"),
            Vgt(0xE3F, [i32("f15f0")]),
            Vgt(0x1112, [i32("f1614")]),
            Vgt(0x1162, [i32("f1618")]),
            Vgt(0x1181, [i32("f161c")]),
            Vgt(0x27D0, [emb("f1c70", "moModel_c.FUN_4c210610")]),
        ]),
    ])
    define_model(reg)
    define_part2(reg)
    define_objects(reg)
    reg.define("moPart_c", [
        Vgt(0xC7C, [
            base("moPart_c.FUN_4c2309d0"),
            base("moPart_c.FUN_4c2378b0"),
            Cond(0x80, [Old("moDownstreamIdData_c under condition 0x80")]),
        ], [Old("moModel_c::Serialize pre-0xc7d")]),
    ])
    reg.define("gcXhatch_c", [
        cstr("f08"),
        f64("f10"),
        f64("f18"),
        Vge(0x3CD, [i32("f34")]),
        Vgt(0x7D6, [i32("f20")]),
        Vgt(0x916, [i32("f24")]),
        Vge(0x278A, [i32("f28"), i32("f2c")]),
        Vge(0x27B0, [i32("f30")]),
    ])
    reg.define("gcCurvatureObject_c", [
        f64("f08"), f64("f10"), f64("f18"), f64("f20"), f64("f28"),
        u32("f58"),
        u32("f5c"),
    ])
    reg.define("moTransRefPlaneData_c", [
        i32("f08"), i32("f0c"), u32("f10"), u32("f14"), i32("f18"), u32("f1c"),
    ])
    reg.define("moMaterial_c", [
        obj("f08"),
        Vgt(0x2B90, [Vlt(0x2BAB, [f64(f"f{k:02x}") for k in range(0x10, 0x48, 8)])]),
    ])
    reg.define("uoModelData_c", [
        Vgt(0x99, [
            Vlt(0x17D, [Old("uoModelData_c lights pre-0x17d")]),
            obj("f08"),
        ]),
        Vgt(0x1BD, [i32("f10")]),
    ])
    reg.define("moParameter_c.FUN_4c17a330", [
        Vgt(0xC7C, [base(NODE_LW)], [Old("moNode_c::Serialize pre-0xc7d")]),
        Vlt(0x218, [obj("old_units")]),
        Vgt(0x6A, [Vlt(0xDB9, [i32("old_6a")]), obj("f48")]),
        Vgt(0xA9C, [Vlt(0xDB9, [i32("old_a9c")])]),
    ])
    for c in ("moLengthParameter_c", "moDensityParameter_c"):
        reg.define(c, [
            base("moParameter_c.FUN_4c17a330"),
            f64("f58"),
            NCond(0x80, [Vgt(0x3DA, [u8("f68"), Nz("f68", [f64("f60")])])]),
        ])
    reg.define("moUnitComponent_c", [
        base("moComponent_c"),
        Cond(1, [Old("moUnitComponent_c condition 1")]),
        u8("has_ext"),
        Nz("has_ext", [obj("ext")], [Vlt(0x3B3, [obj("old_model")])]),
    ])


def neg(field):
    return lambda s, ar: s[field] < 0


def define_atom(reg):
    vt(0x4B8, "moAtom_c", CONCEPT_LW)
    vt(0x4C0, "moAtom_c", CONCEPT_RES)
    reg.define("moAtom_c", [
        Vlt(0x7F2, [Old("moAtom_c su_CObject base pre-0x7f2")], [base("moNode_c.SerializeNode")]),
        Vlt(0x488, [Old("moAtom_c pre-0x488")]),
        i32("f140"),
        Norm("u32", "f144", lambda v, ar: 0 if not cond(ar, 0x80) and v > 1 else v),
        Vlt(0x86F, [Old("moAtom_c feature refs pre-0x86f")], [i32("f130"), i32("f12c"), u32("f158")]),
        i32("body_kind"),
        If(lambda s, ar: s["body_kind"] == 1, [
            emb("f160", "mo_loadBodyFromArchive"),
            emb("f120", "suObList"),
        ]),
        If(lambda s, ar: s["body_kind"] == 2, [i32("f160")]),
        Vge(0x4B4, [
            Vlt(0x4C2, [Old("moAtom_c 0x4b4-0x4c1 body")], [
                i32("f170"),
                Vge(0x7F2, [
                    Vgt(0x87F, [i32("f18c")]),
                    Vgt(0x8DF, [i32("f198")]),
                ]),
            ]),
        ]),
        If(lambda s, ar: ar.ctx.get("conditions", 0) == 0 or cond(ar, 0x400000), [
            Vgt(0x8DD, [i32("f180"), i32("f188"), i32("f1b0")]),
        ]),
        Vge(0xF3D, [i32("f19c")]),
    ])


def define_model(reg):
    define_atom(reg)
    reg.define("moAtomManager_c.FUN_4bcef8d0", [
        Vgt(0x487, [
            i32("f260"),
            Len("i32", "n6c", "atoms"),
            Rep(Pos("n6c"), "atoms", [obj("o")]),
            Vgt(0x74C, [u32("fa8")]),
        ]),
    ])
    reg.define("moGhostBodyObject_c.FUN_4bf05390", [
        i32("f08"),
        i32("f0c"),
        i32("f10"),
        i32("fc0"),
        Vgt(0xF6C, [
            Len("i32", "nb0", "fa0"),
            Rep(Pos("nb0"), "fa0", [i32("v")]),
        ]),
        Vgt(0xF80, [ObjIf("i32", "has_f50", "f50")]),
        Vgt(0xF8B, [
            Len("i32", "nf0", "ff0"),
            Rep(Pos("nf0"), "ff0", [emb("p", "mgPoint_c.restore")]),
        ]),
    ])
    reg.define("moGhostBodyIdManager_c.FUN_4bf050e0", [
        i32("f80"),
        Vgt(0xF09, [
            GhostCount(),
            Rep(Pos("n"), "objects", [emb("o", "moGhostBodyObject_c.FUN_4bf05390")]),
        ]),
    ])
    reg.define("mo3DPrintSettings_c.FUN_4b541b90", [
        f64("f08"), f64("f10"), f64("f18"), f64("f20"),
        i32("f28"),
        obj("f00"),
    ])
    reg.define("moModel_c.FUN_4c234150", [
        base(CONCEPT_RES),
        Vgt(0x21A, [emb("fd88", "moAtomManager_c.FUN_4bcef8d0")]),
        Vgt(0xDA5, [emb("fd90", "moGhostBodyIdManager_c.FUN_4bf050e0")]),
        If(lambda s, ar: 0x1295 < ver(ar) < 0x12FE and not s.get("f161c", 0), [], [obj("f9d0")]),
        Vgt(0x725, [emb("fb08", "su_CObArray")]),
        Vlt(0x46, [Old("moDetailDefs_c pre-0x46")], [emb("fae0", "moDetailDefs_c")]),
        Vgt(0x21C, [emb("f9c8", "su_CObArray")]),
        Vgt(0x406, [obj("f1e0")]),
        Vlt(0xF98, [Old("moUnitsTable_c f9b8 pre-0xf98")]),
        Vgt(0x38D, [obj("f9c0")], [Old("moUnitsTable_c f9c0 pre-0x38e")]),
        obj("f9d8"),
        Vgt(0x1BF4, [Vlt(0x3734, [Old("FUN_4c234150 plane map 0x1bf5-0x3733")])]),
        Vlt(0x22E, [Old("moView_c array pre-0x22e")], [Rep(lambda s, ar: 10, "f9f8", [obj("o")])]),
        Vlt(0x3B3, [Old("moConfigurationMgr_c pre-0x3b3")]),
        Vgt(0x773, [Norm("u8", "fd2c", lambda v, ar: 0)]),
        Vgt(0x778, [i32("fce8"), i32("fcec")]),
        Vgt(0x139, [Vlt(0x227, [Old("su_CStringArray 0x13a-0x227")])]),
        Vgt(0x1B7, [obj("fa88")]),
        Vgt(0x2C7, [obj("attach")]),
        Vgt(0x71C, [Norm("i32", "fd44", lambda v, ar: max(v, 10))]),
        Vgt(0x74C, [Present("i32", "has_fdb8", "fdb8", [emb("fdb8", "moNodeList_c.Serialize")])]),
        Vlt(0x7EE, [Old("moPosGroupFolder_c pre-0x7ee")]),
        Vgt(0x8D1, [Norm("i32", "fd48", lambda v, ar: max(v, 0))]),
        Vgt(0x8DB, [obj("fe80")]),
        Vgt(0xB57, [obj("fa48")]),
        Vgt(0xB8D, [i32("feb0")]),
        Vgt(0xBC6, [
            i32("feb4"),
            Len("i32", "nec8", "fec0"),
            Rep(Pos("nec8"), "fec0", [u32("v")]),
        ]),
        Vgt(0xBD0, [obj("fa90")]),
        Vgt(0xE2C, [u32("ff3c")]),
        Vgt(0x2BAF, [
            Len("i32", "n1290", "f1288"),
            Rep(Pos("n1290"), "f1288", [u32("v")]),
        ]),
        Vgt(0x917, [
            emb("fb30", "su_CObArray"),
            emb("fba8", "su_CObArray"),
            emb("fb58", "su_CObArray"),
            emb("fb80", "su_CObArray"),
        ]),
        Vgt(0xF13, [
            emb("fbf8", "su_CObArray"),
            emb("fbd0", "su_CObArray"),
            emb("fc20", "su_CObArray"),
        ]),
        Vgt(0xF23, [emb("fc70", "su_CObArray")]),
        Vgt(0xA75, [Vlt(0xD7B, [Old("FUN_4c78c320 0xa76-0xd7a")])]),
        Vgt(0xC7C, [obj("fed0")]),
        Vgt(0xDA1, [emb("f240", "moForwardedFeatRefsList_c.FUN_4bb5ced0")], [Old("FUN_4c234150 pre-0xda2 tail")]),
        Vgt(0xF51, [If(lambda s, ar: not cond(ar, 0x80) or cond(ar, 0x400000), [obj("fe38")])]),
        Vgt(0x10E5, [
            i32("f1010"),
            Len("i32", "nff4", "ffe0"),
            Rep(Pos("nff4"), "ffe0", [obj("k"), Norm("i32", "v", lambda v, ar: int(v != 0))]),
        ]),
        Vgt(0x10EB, [PartOnly([i32("f1014")])]),
        Vgt(0x12B7, [
            Len("i32", "n10c4", "f10b0"),
            Vlt(0x12BB, [Old("FUN_4c234150 0x10b0 map pre-0x12bb")]),
            If(lambda s, ar: s["n10c4"] > 0 and not (s["f2c"] & 0x100), [Old("FUN_4c234150 0x10b0 map without node flag 0x100")]),
            Rep(Pos("n10c4"), "f10b0", [i32("hi"), i32("lo"), i32("a"), i32("b")]),
        ]),
        PartOnly([
            Vgt(0x146F, [i32("f1104")]),
            Vgt(0x1437, [
                Len("i32", "n1118", "f1108"),
                Rep(Pos("n1118"), "f1108", [emb("o", "moDimIncrementId_c.Serialize")]),
            ]),
            Vgt(0x1C0B, [
                i32("f1128"),
                Len("i32", "n1140", "f1130"),
                Rep(Pos("n1140"), "f1130", [emb("o", "moDimIncrementId_c.Serialize")]),
            ]),
        ]),
        Vgt(0x1480, [i32("fb00")]),
        Vgt(0x1FC6, [i32("fd54")]),
        Vgt(0x1FF1, [Present("i32", "has_f1270", "f1270", [emb("f1270", "mo3DPrintSettings_c.FUN_4b541b90")])]),
        Vgt(0x2397, [obj("fa50"), i32("feb8")]),
        Vgt(0x27D3, [cstr("f760"), cstr("f768")]),
        Vgt(0x27DE, [obj("f12d0")]),
        Vgt(0x2B65, [obj("f1338")]),
        Vgt(0x3B05, [
            Len("i32", "n1d8", "f1d0"),
            Rep(Pos("n1d8"), "f1d0", [
                cstr("k0"),
                cstr("k1"),
                Len("i32", "m", "pairs"),
                Rep(Pos("m"), "pairs", [i32("a"), i32("b")]),
            ]),
        ]),
    ])
    reg.define("moForwardedFeatRefsList_c.FUN_4bb5ced0", [base("suObList")])


def define_part2(reg):
    reg.define("moMassProp_c.Serialize", [
        f64("f20"), f64("f28"), f64("f30"), f64("f10"), f64("f08"), f64("f18"),
        f64("f38"), f64("f40"), f64("f48"), f64("f50"), f64("f60"), f64("f58"),
        Vgt(0x7D6, [i32("f1c0")]),
        Vgt(0x85C, [i32("f1c4")]),
        Vgt(0xA16, [i32("f1c8")]),
        Vgt(0xA97, [Norm("i32", "f1cc", lambda v, ar: int(v > 0))]),
        Vgt(0x10F0, [
            i32("f1e0"),
            Vgt(0x116A, [
                Vlt(0x11D4, [Old("moMassProp_c 0x116b-0x11d3")]),
                Vgt(0x11D5, [f64("f00")]),
                Vgt(0x13FA, [
                    i32("f134"), i32("f138"), i32("f13c"), i32("f140"),
                    cstr("f148"), cstr("f150"),
                    Vlt(0x13FF, [Old("moMassProp_c f1f0 pre-0x13ff")], [i32("f1f0")]),
                    Vgt(0x1459, [f64("fc8"), f64("fd0"), f64("fd8")]),
                    Vgt(0x1460, [
                        emb("f68", "mgVector_c.restore"),
                        emb("f80", "mgVector_c.restore"),
                        emb("f98", "mgVector_c.restore"),
                    ]),
                    Vgt(0x1470, [i32("f15c")]),
                    Vgt(0x1FB5, [u16("f128")]),
                ]),
            ]),
        ]),
    ])
    reg.define("moMassPropCache_c.Serialize", [
        Len("i32", "n10", "f08"),
        Rep(Pos("n10"), "f08", [i32("atom"), i32("v"), f64("d")]),
        If(lambda s, ar: s["n10"] != 0, [
            emb("f18", "moMassProp_c.Serialize"),
        ]),
    ])
    reg.define("moPart_c.FUN_4c2378b0", [
        Section(2, [
            base("moModel_c.FUN_4c234150"),
            i32("f14f8"),
            u8("f1428"),
            i32("f14d8"),
            Vgt(0xCA8, [Norm("i32", "f152c", lambda v, ar: v if ver(ar) >= 0xDE0 else 0)]),
            Vgt(0x1190, [If(lambda s, ar: not cond(ar, 0x80) and not cond(ar, 1) and not cond(ar, 0x80000000), [MassCaches()])]),
            Vgt(0x12A0, [i32("f1400"), obj("f13f8")]),
            Vgt(0x12E7, [i32("f1698")]),
            Vgt(0x1416, [i32("f169c")]),
            Vgt(0x145A, [Present("i32", "has_f16b8", "f16b8", [
                Len("u32", "n16b8", "f16b8"),
                Rep(lambda s, ar: s["n16b8"] & 0xFFFFFFFF, "f16b8", [i32("k"), obj("o")]),
                Len("i32", "n16d0", "f16d0"),
                Rep(Pos("n16d0"), "f16d0", [i32("k"), u8("v")]),
            ])]),
            Vgt(0x1481, [
                Len("i32", "n16f8", "f16e8"),
                Rep("n16f8", "f16e8", [obj("o")]),
            ]),
            Vgt(0x1FA4, [If(lambda s, ar: not cond(ar, 0x80) and not cond(ar, 1) and s["f161c"] == 0, [BBoxCache()])]),
            Vgt(0x238D, [i32("f18d4")]),
            Vgt(0x2410, [u32("f18d8")]),
            Vgt(0x23DF, [i32("f1900")]),
            Vgt(0x2795, [
                i32("f1be0"),
                If(lambda s, ar: s["f1be0"] != 0, [
                    Len("i32", "n1b98", "f1bc8"),
                    Rep(Pos("n1b98"), "f1bc8", [i32("v")]),
                ]),
            ]),
        ]),
    ])


def define_lights(reg):
    for c in ("moAmbientLight_c", "moDirectionLight_c"):
        concept_vt(c)
    reg.define("moLightFeature_c.FUN_4bc0b030", [
        Vlt(0x1168, [Old("light feature pre-0x1168")], [base("moModelFeature_c")]),
        f64("f390"),
        f64("f398"),
        f64("f3a0"),
        u32("f3a8"),
        Norm("i32", "state", lambda v, ar: int(v != 0)),
        i32("f428"),
        Norm("i32", "f36c", lambda v, ar: 0),
        Vge(0x452, [i32("f4f0")]),
        Vge(0x17D, [cstr("f4f8")], [Old("light name pre-0x17d")]),
        Vlt(0x407, [Old("light user name pre-0x407")]),
        Vge(0x1196, [Shadow("i32", "f384", 0)], [Old("light f384 pre-0x1196")]),
        Vgt(0xD01, [i32("f388")]),
        Vgt(0x11A3, [i32("f384"), f64("f478"), i32("f488"), f64("f490")]),
        emb("f500", "moUserProperty_c.restore"),
    ])
    reg.define("moAmbientLight_c", [base("moLightFeature_c.FUN_4bc0b030")])
    reg.define("moDirectionLight_c", [
        base("moLightFeature_c.FUN_4bc0b030"),
        Vgt(0x427, [emb("f3b0", "mgVector_c.restore")]),
        Vge(0x11A4, [f64("f498")]),
    ])


def define_objects(reg):
    define_lights(reg)
    reg.provisional("moFeatColorTab_c", [
        Len("u32", "n", "items"),
        If(lambda s, ar: s["n"] != 0, [
            Vlt(0x1D9, [Old("moFeatColorTab_c colors pre-0x1d9")]),
        ]),
        Rep(lambda s, ar: max(s["n"] - (1 << 32) if s["n"] >= 1 << 31 else s["n"], 0), "items", [
            emb("vp", "moVisualProperties_c.restore"),
            i32("v"),
        ]),
    ])
    vt(0x3E8, "moSketchBlockMgr_c", None)
    vt(0x3F8, "moSketchBlockMgr_c", True)
    vt(0x4B8, "moSketchBlockMgr_c", CONCEPT_LW)
    vt(0x4C0, "moSketchBlockMgr_c", CONCEPT_RES)
    reg.provisional("moRefIdToSketchBlockListMap_c.FUN_4c9080f0", [
        i32("f18"),
        obj("f30"),
        Len("i32", "n70", "f68"),
        If(lambda s, ar: s["n70"] > 0, [
            Vlt(0xA5B, [Old("sketch block list map pre-0xa5b")]),
            Rep(Pos("n70"), "f68", [
                i32("key"),
                Len("i32", "m", "guids"),
                Rep(Pos("m"), "guids", [Raw("g", 16)]),
            ]),
        ]),
        Vgt(0xBBC, [
            Len("u32", "n98", "f90"),
            Rep(lambda s, ar: s["n98"] if s["n98"] < 0x80000000 else 0, "f90", [
                Raw("k", 16),
                Raw("v", 16),
                i32("i"),
                cstr("name"),
            ]),
        ]),
    ])
    reg.provisional("moSketchBlockMgr_c", [
        base("moFeature_c"),
        Raw("f380", 16),
        emb("blocks", "moRefIdToSketchBlockListMap_c.FUN_4c9080f0"),
    ])
    reg.provisional("suUIntArray.Serialize", [
        i32("n"),
        i32("f18"),
        Raw("data", lambda s, ar: max(s["n"], 0) * 4),
    ])
    reg.provisional("moLayerMask_c", [
        emb("f08", "suUIntArray.Serialize"),
        Vlt(0x1BE5, [Old("moLayerMask_c remap pre-0x1be5")]),
    ])
    reg.provisional("moLayerMgr_c", [
        Len("u32", "n", "layers"),
        Rep("n", "layers", [obj("o")]),
        obj("f08"),
        NCond(1, [Vgt(0x438, [Vlt(0xC65, [Old("moLayerMgr_c drawing ref pre-0xc65")], [obj("f30")])])]),
        Vgt(0x446, [obj("f20")]),
        Vgt(0xFB8, [i32("f38")]),
    ])
    reg.provisional("su_CMapStringToString", [
        count("n"),
        Rep("n", "items", [cstr("k"), cstr("v")]),
    ])
    reg.provisional("moBendNoteFormat_c", [cstr("f08"), obj("f10")])
    reg.provisional("mgPoint_c.stream", [f64("x"), f64("y"), f64("z")])
    reg.provisional("moCachedBoundingBoxData_c", [
        i32("fc0"),
        Rep(lambda s, ar: 2, "boxes", [
            i32("id"),
            Norm("i32", "set", lambda v, ar: int(v != 0)),
            If(lambda s, ar: s["set"] != 0, [emb("lo", "mgPoint_c.stream"), emb("hi", "mgPoint_c.stream")]),
        ]),
    ])
    reg.provisional("moGhostGeometricData_c", [Vgt(0xF4A, [i32("f08")])])
    reg.provisional("moCThreadRefMgr_c", [
        Len("i32", "n", "f18"),
        Rep(Pos("n"), "f18", [
            i32("key"),
            Len("u32", "m", "holders"),
            Rep(lambda s, ar: s["m"], "holders", [obj("o")]),
        ]),
        Vgt(0x3755, [Norm("i32", "f1a0", lambda v, ar: int(v != 0))]),
    ])
    reg.provisional("su_CMapWordToOb.Serialize", [
        count("n"),
        Rep("n", "items", [u16("k"), obj("v")]),
    ])
    concept_vt("moPrtExplViewManager_c")
    reg.provisional("moPrtExplViewManager_c", [
        base("moFeature_c"),
        obj("f358"),
        obj("f360"),
        Vgt(0xAC8, [f64("f398"), i32("f3a0"), i32("f3a4")]),
        emb("f368", "su_CMapWordToOb.Serialize"),
    ])
    reg.provisional("moAnnotationView_c", [
        base("moView_c"),
        Vgt(0xB68, [i32("f3d8")]),
        Vgt(0xB79, [obj("f3d0")]),
        Vgt(0xBC6, [Vlt(0xC8C, [Old("moAnnotationView_c vector pre-0xc8c")])]),
        Vgt(0xBE0, [ObjShadow("f3e8", 0)]),
        Vgt(0xBE3, [i32("f3f0")]),
        Vgt(0xC8B, [f64("f3e0")]),
        Vgt(0xCC3, [obj("f3e8")]),
        Vgt(0xCE0, [i32("f3f4"), i32("f3f8")]),
        Vgt(0x238F, [obj("f2f0")]),
        Vgt(0x2B7E, [i32("f3fc")]),
        Vgt(0x2B9A, [i32("f408")]),
        Vgt(0x2BA0, [i32("f400")]),
        Vgt(0x2BBB, [i32("f404")]),
    ])
    reg.provisional("moFlatPatternColorTab_c", [
        u32("f08"), u32("f0c"), u32("f10"), u32("f14"), u32("f18"),
        Vgt(0xC8F, [u32("f1c")]),
        Vgt(0x11D3, [u32("f20")]),
        Vgt(0x12AD, [u32("f24")]),
    ])
    concept_vt("moEnvFolder_c")
    reg.provisional("moEnvFolder_c", [base("moFolder_c")])
    reg.define("RelCacheDimValueMap_c.Serialize", [
        Vge(0x856, [
            count("n"),
            Rep("n", "items", [cstr("k"), f64("v")]),
        ]),
    ])
    reg.define("moRelMgr_c", [
        emb("f58", "suObList"),
        emb("f10", "RelCacheDimValueMap_c.Serialize"),
        Vgt(0x1166, [cstr("f170"), i32("f178")]),
        Vgt(0x116E, [time32("f180")]),
        Vge(0x12AA, [i32("f150")]),
        Vgt(0x1311, [i32("ff4")]),
        Vgt(0x23BD, [emb("fa0", "suObList")]),
        Vgt(0x336A, [
            i32("f1b0"),
            Len("u32", "n1c0", "f1c0"),
            Rep(lambda s, ar: s["n1c0"], "f1c0", [obj("o")]),
        ]),
    ])
