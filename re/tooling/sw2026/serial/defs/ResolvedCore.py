from __future__ import annotations

from Core import ArchiveError, Obj, Load, Store, BIG_TAG, BIG_CLASS, CLASS_TAG, NEW_CLASS, NULL_TAG
from Streams import StreamDoc
from Dsl import Vgt, Vge, Vlt, ver, i32, u32, u16, i16, u8, f64, f32, cstr, emb, base, count
from Schema import Op, If, Rep, run_load, run_store


def ext_class_index(ar):
    p = ar.p
    if ar.left() < 2:
        return None
    tag = int.from_bytes(ar.b[p:p + 2], "little")
    if tag == BIG_TAG:
        big = int.from_bytes(ar.b[p + 2:p + 6], "little")
        if not big & BIG_CLASS:
            return None
        idx = big & 0x7FFFFFFF
    elif tag in (NULL_TAG, NEW_CLASS) or not tag & CLASS_TAG:
        return None
    else:
        idx = tag & 0x7FFF
    if idx in ar.table or idx >= ar.base:
        return None
    return idx


EXT_CONCRETE = {"moComponent_c": "moUnitComponent_c"}


class XO(Op):
    def __init__(self, name, expect=None):
        self.name, self.expect = name, expect

    def read(self, ar):
        idx = ext_class_index(ar)
        if idx is not None:
            known = ar.ctx.get("ext_classes", {}).get(idx)
            name = known or EXT_CONCRETE.get(self.expect, self.expect)
            if name is None:
                raise ArchiveError(f"external class {idx} with no static type at {ar.p}")
            ar.table[idx] = ("class", name, ("ext", idx))
            ar.ctx.setdefault("ext_seen", {})[idx] = name
        return ar.obj()

    def write(self, ar, v):
        if isinstance(v, Obj) and isinstance(v.schema, tuple) and v.schema[0] == "ext":
            ar.classes.setdefault((v.cls, v.schema), v.schema[1])
        ar.obj(v)

    def load(self, ar, scope, o):
        scope[self.name] = self.read(ar)

    def store(self, ar, scope, o):
        self.write(ar, scope[self.name])


def xo(name, expect=None):
    return XO(name, expect)


class Legacy(Op):
    def __init__(self, what):
        self.what = what

    def load(self, ar, scope, o):
        raise ArchiveError(f"legacy path {self.what} not modelled at {ar.p}")

    def store(self, ar, scope, o):
        raise ArchiveError(f"legacy path {self.what} not modelled")


def has_condition(ar, mask):
    flags = ar.ctx.get("conditions", 0)
    if mask == 0:
        return flags == 0
    return (flags & mask) != 0


def Cnd(mask, then, other=()):
    return If(lambda s, ar: has_condition(ar, mask), then, other)


def Ctx(key, then, other=()):
    return If(lambda s, ar: bool(ar.ctx.get(key, 0)), then, other)


def NCtx(key, then, other=()):
    return If(lambda s, ar: not ar.ctx.get(key, 0), then, other)


def Vin(lo, hi, then, other=()):
    return If(lambda s, ar: lo <= ver(ar) < hi, then, other)


VT = {}


def vt(slot, cls, target):
    VT.setdefault(slot, {})[cls] = target


class Virt(Op):
    def __init__(self, slot):
        self.slot = slot

    def target(self, o):
        table = VT.get(self.slot, {})
        if o.cls not in table:
            raise ArchiveError(f"no vtable entry {self.slot:#x} for {o.cls}")
        return table[o.cls]

    def load(self, ar, scope, o):
        t = self.target(o)
        if t is not None:
            ar.registry.run_load(t, ar, scope, o)

    def store(self, ar, scope, o):
        t = self.target(o)
        if t is not None:
            ar.registry.run_store(t, ar, scope, o)


def virt(slot):
    return Virt(slot)


class VIf(Op):
    def __init__(self, slot, then):
        self.slot, self.then = slot, list(then)

    def pred(self, o):
        table = VT.get(self.slot, {})
        if o.cls not in table:
            raise ArchiveError(f"no vtable entry {self.slot:#x} for {o.cls}")
        return bool(table[o.cls])

    def load(self, ar, scope, o):
        if self.pred(o):
            run_load(self.then, ar, scope, o)

    def store(self, ar, scope, o):
        if self.pred(o):
            run_store(self.then, ar, scope, o)


PARENT = {}


def isa(cls, target):
    while cls is not None:
        if cls == target:
            return True
        cls = PARENT.get(cls)
    return False


class OIf(Op):
    def __init__(self, pred, then, other=()):
        self.pred, self.then, self.other = pred, list(then), list(other)

    def load(self, ar, scope, o):
        run_load(self.then if self.pred(o) else self.other, ar, scope, o)

    def store(self, ar, scope, o):
        run_store(self.then if self.pred(o) else self.other, ar, scope, o)


def Kind(target, then, other=()):
    return OIf(lambda o: isa(o.cls, target), then, other)


def pe_noise(s, ar):
    return bool(ar.ctx.get("pe_active", 0) and ar.ctx.get("pe_helper", 0)) or bool(ar.ctx.get("pe_file", 0))


def obarray(name):
    return emb(name, "rf.suObArray")


CONCEPT_LW = "moConcept_c.SerializeLWData"
CONCEPT_RES = "moConcept_c.SerializeResolvedData"
NODE_LW = "moNode_c.SerializeLWData"
FEATURE_XML = "moFeature_c.SerializeXmlData"


def concept_vt(cls, xml=FEATURE_XML):
    vt(0x4B8, cls, CONCEPT_LW)
    vt(0x4C0, cls, CONCEPT_RES)
    vt(0x3F8, cls, True)
    vt(0x3E8, cls, xml)


def node_vt(cls):
    vt(0x4B8, cls, NODE_LW)
    vt(0x4C0, cls, None)
    vt(0x3F8, cls, True)
    vt(0x3E8, cls, None)


DOC_CTX = {"model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": 1}
MBSM = "moPartConfiguration_c.SerializeMBSMDataObjects"


def mbsm_present(ar):
    return bool(ar.ctx.get("model_is_part", 0) and ar.ctx.get("cmgr_f658", 0))


def load_resolved(data, reg, version=None, *, archive=None, name=None):
    ar = Load(data, 1, reg, version, dict(DOC_CTX))
    head = ar.prim("u32")
    ar.count = head
    ar.base = head
    n = ar.count_value()
    roots = [XO("o").read(ar) for _ in range(n)]
    hd = {"base": head, "n": n}
    if mbsm_present(ar):
        m = Obj(MBSM)
        reg.run_load(MBSM, ar, m.f, m)
        hd["mbsm"] = m
    rest = ar.raw(ar.left())
    return StreamDoc("resolved", hd, roots, rest), ar


def store_resolved(doc, reg, version=None):
    ar = Store(doc.head["base"], reg, version, dict(DOC_CTX))
    ar.prim("u32", doc.head["base"])
    ar.count_value(len(doc.roots))
    for o in doc.roots:
        XO("o").write(ar, o)
    if "mbsm" in doc.head:
        m = doc.head["mbsm"]
        reg.run_store(MBSM, ar, m.f, m)
    ar.raw(doc.tail)
    return bytes(ar.out)


PLANS = {"Contents/Config-0-ResolvedFeatures": ("custom", (load_resolved, store_resolved))}


def define(reg):
    reg.define(MBSM, [
        Vgt(0x140A, [
            Vlt(0x141E, [i32("fccc")]),
            u32("n"),
            Rep("n", "fcd8", [i32("key"), xo("o")]),
        ]),
    ])
    reg.define("rf.suObArray", [count("n"), Rep("n", "items", [xo("o")])])
    reg.define("rf.suObList", [count("n"), Rep("n", "items", [xo("o")])])
    reg.define("moNodeList_c.Serialize", [emb("list", "rf.suObList"), i32("tail")])
    reg.define(NODE_LW, [
        xo("f18", "moNodeName_c"),
        Vlt(0x6B, [], [i32("f0c")]),
        Vgt(0xE1, [u32("f28")]),
        Vgt(0x147, [i32("f08")]),
        Vgt(0x143A, [i32("f2c")]),
        Vgt(0x23CD, [cstr("f20")]),
    ])
    reg.define(CONCEPT_LW, [
        base(NODE_LW),
        Vgt(0xC7C, [
            i32("has_list68"),
            If(lambda s, ar: s["has_list68"] != 0, [emb("f68", "moNodeList_c.Serialize")]),
        ]),
        Vgt(0x1A5, [xo("f78", "moVisualProperties_c")]),
    ])
    reg.define(CONCEPT_RES, [
        NCtx("ctx874", [
            emb("f60", "moNodeList_c.Serialize"),
            Vgt(0x9FD, [Vlt(0xD7B, [Legacy("moConcept_c.SerializeResolvedData old node list")])]),
        ]),
    ])
    reg.define("moNode_c", [
        Vgt(0xC7C, [virt(0x4B8), virt(0x4C0)], [Legacy("moNode_c::Serialize pre-0xc7d")]),
    ])
    reg.define("moNode_c.SerializeNode", [
        Vgt(0xC7C, [virt(0x4B8), virt(0x4C0)], [Legacy("moNode_c::Serialize (FUN_4c177c00 pre-0xc7d)")]),
    ])
    reg.define(FEATURE_XML, [
        Cnd(0x180A1, [cstr("f200")]),
    ])
    reg.define("utLineWidth_c.Serialize2", [
        Vge(0xF41, [i16("f06"), f32("f00")], [i16("f06")]),
    ])
    reg.define("moVisProp_c", [u32("f00"), u16("f04"), emb("f08", "utLineWidth_c.Serialize2")])
    reg.define("moEntVisProp_c", [
        u16("f00"),
        u16("f02"),
        Vgt(0x446, [u8("f04")]),
        emb("f08", "moVisProp_c"),
    ])
    reg.define("moFeature_c", [
        base("moNode_c.SerializeNode"),
        i32("f298"),
        Vgt(0x184, [i32("f28c")]),
        Vgt(0x96, [u32("f29c"), Vlt(0x43B, [u32("old_43b")])]),
        Vgt(0x139, [
            u8("has_f1e8"),
            If(lambda s, ar: s["has_f1e8"] != 0, [cstr("f1e8")]),
        ]),
        Vgt(0x17D, [i32("f2a8")]),
        Vlt(0x1DD, [], [i32("f2b8"), i32("f2bc")]),
        Vlt(0x2FC, [], [i32("f2b0")]),
        Vgt(0x3A9, [f64("f1e0")]),
        Vlt(0x3D6, [], [i32("f2b4")]),
        Cnd(1, [i32("cond1_a"), i32("cond1_b")]),
        Vgt(0x401, [xo("f258", "moFolder_c")]),
        Vgt(0x7DA, [cstr("f1f8")]),
        Vlt(0x7E8, [], [u8("f1f4")]),
        Vgt(0x808, [emb("f2c8", "moEntVisProp_c")]),
        If(pe_noise, [Cnd(0, [u8("pe_noise")])]),
        Vgt(0x925, [i32("f2ec")]),
        Vgt(0x99C, [i32("fa8")]),
        Vgt(0xA2A, [xo("f2f0", "moFeatComment_c")]),
        Vgt(0xA54, [Vlt(0xA69, [
            u8("old_a69"),
            If(lambda s, ar: s["old_a69"] != 0, [cstr("old_a69_s")]),
        ])]),
        Vgt(0xA68, [u32("f208")]),
        Vgt(0xACA, [u8("f300"), u8("f301")]),
        Vlt(0xC50, [], [i32("f318")]),
        Vgt(0xC55, [i32("hidden")]),
        Vgt(0xF61, [i32("f30c")]),
        Vgt(0x11CC, [i32("f2a4"), i32("f2a0")]),
        Vgt(0x11DA, [u16("f98")]),
        Vgt(0x23FA, [i32("f2ac")]),
        Vgt(0x279B, [i32("f344")]),
        VIf(0x3F8, [virt(0x3E8)]),
    ])
    reg.define("moFeature_c.FUN_4bb2b240", [
        Vin(0x393, 0x3AF, [Legacy("FUN_4bb2b240 old id keeper")]),
    ])
    reg.define("moModelFeature_c", [
        base("moFeature_c"),
        base("moFeature_c.FUN_4bb2b240"),
        Vgt(0xDB2, [i32("f35c")]),
    ])
    reg.define("moFolder_c", [
        base("moFeature_c"),
        Vgt(0xA92, [i32("f360")]),
        Vge(0x27B4, [i32("f370")]),
    ])
