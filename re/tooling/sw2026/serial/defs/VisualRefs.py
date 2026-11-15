from __future__ import annotations

from Core import ArchiveError
from Dsl import Vgt, Vge, Vlt, ver, i32, u32, u16, u8, f64, cstr, obj, rep, base, emb, time32
from Schema import If, Fn


def legacy(what):
    def fail(ar, scope, o):
        raise ArchiveError(f"legacy branch {what} not modelled at {getattr(ar, 'p', '?')}")
    return Fn(fail, fail)


def condition(mask):
    return lambda s, ar: (ar.ctx.get("conditions", 0) & mask) != 0


def Vin(lo, hi, then):
    return If(lambda s, ar: lo < ver(ar) < hi, then)


def positive(field):
    return lambda s, ar: max(s[field], 0)


def define_surf_ids(reg):
    reg.provisional("moFRKeeper_c.Serialize", [
        obj("f08"),
        obj("f10"),
    ])
    reg.provisional("moEntityId_c.Serialize", [
        Vlt(0x180, [legacy("moEntityId_c flag byte pre-0x180")]),
        obj("f08"),
    ])
    reg.provisional("moSurfIdRep_c.FUN_4bba8790", [
        Vgt(0x21A, [emb("f10", "moFRKeeper_c.Serialize")], [legacy("moSurfIdRep_c pre-0x21b")]),
    ])
    two = [i32("f38"), i32("f3c")]
    three = [i32("f38"), i32("f3c"), i32("f40")]
    for cls, own in (
        ("moEndFace3IntSurfIdRep_c", three),
        ("moFromSktEnt3IntSurfIdRep_c", three),
        ("moEndFaceSurfIdRep_c", two),
        ("moSweepSideSurfIdRep_c", two),
        ("moThinClosingSurfIdRep_c", two),
        ("moWzdHoleSurfIdRep_c", two),
    ):
        reg.provisional(cls, [base("moSurfIdRep_c.FUN_4bba8790"), *own])
    for cls in ("moFilletSurfIdRep_c", "moFromSktEntSurfIdRep_c", "moThinOffsetSurfIdRep_c"):
        reg.provisional(cls, [base("moSurfIdRep_c.FUN_4bba8790"), i32("f38")])
    reg.provisional("moSurfIdRep_c.FUN_4bba9f70", [
        base("moSurfIdRep_c.FUN_4bba8790"),
        If(lambda s, ar: ar.ctx.get("helper_20", 0) != 0, [legacy("FUN_4bba9f70 helper+0x20 set")]),
        Vlt(0x180, [legacy("FUN_4bba9f70 pre-0x180")]),
        emb("f38", "moEntityId_c.Serialize"),
    ])
    for cls in ("moShellSurfIdRep_c", "moIndirectSurfIdRep_c", "moMirPatternSurfIdRep_c"):
        reg.provisional(cls, [base("moSurfIdRep_c.FUN_4bba9f70")])
    reg.provisional("moCirPatternSurfIdRep_c", [
        base("moSurfIdRep_c.FUN_4bba9f70"),
        i32("f48"),
        Vin(0x23EB, 0x23EF, [i32("old_23eb")]),
    ])


def define_ent_refs(reg):
    reg.provisional("moEntRefDownstreamIdData_c.Serialize", [
        i32("n10"),
        rep(positive("n10"), "f10", [i32("key"), i32("value")]),
        i32("n20"),
        rep(positive("n20"), "f20", [i32("v")]),
        i32("f38"),
        Vgt(0x3358, [i32("f40_0"), i32("f40_1")]),
    ])
    reg.provisional("moBEntRef_c", [
        u32("f60"),
        u32("f64"),
        u32("f08"),
        Vge(0x20C, [i32("fe8")]),
        Vgt(0x496, [u32("f70")]),
        Vin(0x8CB, 0xA05, [legacy("moBEntRef_c 0x8cc-0xa04 edge ref")]),
        Vin(0x991, 0xA05, [legacy("moBEntRef_c 0x992-0xa04 vertex ref")]),
        Vgt(0xA04, [f64("f28"), f64("f30"), obj("f40")]),
        Vin(0x931, 0xBE8, [legacy("moBEntRef_c 0x932-0xbe7 object")]),
        If(lambda s, ar: ar.ctx.get("helper_48", 0) != 0, [legacy("moBEntRef_c FUN_4bbac610 ids")]),
        rep("f08", "f10", [emb("id", "moEntityId_c.Serialize")]),
        Vgt(0x536, [
            u32("f48"),
            If(lambda s, ar: ver(ar) < 0x542 and s["f48"] > 0, [legacy("moBEntRef_c pre-0x542 ids")]),
        ]),
        Vgt(0x23BB, [
            i32("nd0"),
            rep(positive("nd0"), "fd0", [time32("a"), time32("b")]),
        ]),
        Vgt(0x332C, [
            i32("fec"),
            i32("has_f18"),
            If(lambda s, ar: s["has_f18"] != 0, [emb("f18", "moEntRefDownstreamIdData_c.Serialize")]),
        ]),
    ])
    reg.provisional("moFaceRef_c", [
        base("moBEntRef_c"),
        If(condition(0x80), [], [
            Vgt(0x109B, [
                i32("nf0"),
                rep(positive("nf0"), "ff0", [
                    i32("f08"),
                    Vlt(0x10E3, [i32("f0c")], [u32("f0c")]),
                    u32("f10"),
                    i32("f14"),
                ]),
            ]),
        ]),
    ])
    reg.provisional("moEdgeRef_c", [base("moBEntRef_c")])
    reg.provisional("moCompBEntRef_c", [
        base("moCompRef_c"),
        Vlt(0x180, [legacy("moCompBEntRef_c pre-0x180")]),
        u8("alias"),
        If(lambda s, ar: s["alias"] == 0, [obj("fe8")], [
            cstr("f08"),
            Vgt(0x45F, [obj("fe8")]),
        ]),
        If(lambda s, ar: 0x9D <= ver(ar) <= 0xAA or ver(ar) >= 0xB3, [obj("ff0")]),
    ])
    reg.provisional("moCompFace_c", [base("moCompBEntRef_c")])


def define_chain_components(reg):
    reg.provisional("moChainComponent_c", [
        base("moComponent_c"),
        obj("f20"),
        Vge(0x837, [u32("f30")]),
    ])
    reg.provisional("moContextChainComponent_c", [
        base("moChainComponent_c"),
        obj("f40"),
        Vge(0x38D, [i32("f48")]),
    ])
    reg.provisional("moReferenceChain_c", [
        If(condition(0x80000001), [], [Vlt(0x3B3, [legacy("moReferenceChain_c model pre-0x3b3")])]),
        Vgt(0x75, [u16("f24")]),
        If(condition(0x80000001), [i32("has_f18")]),
        If(lambda s, ar: ver(ar) < 0x144 and s.get("f24", 0) != 2, [legacy("moReferenceChain_c moReference_c pre-0x144")]),
        obj("f08"),
        i32("f20"),
        Vgt(0x8D1, [emb("f40", "moReferencedConfiguration_c")]),
    ])
    reg.provisional("moExtFeatureList_c", [
        Vlt(0xF21, [legacy("moExtFeatureList_c CObList pre-0xf21")]),
        i32("n"),
        rep(lambda s, ar: s["n"] & 0xFFFFFFFF, "f08", [obj("o")]),
    ])
    reg.provisional("moExtObjectInterface_c.FUN_4c179410", [
        Vlt(0xF25, [legacy("moExtObjectInterface_c pre-0xf25")]),
        emb("f10", "moSharedFileDef_c"),
        emb("f18", "moReferencedConfiguration_c"),
        u8("f40"),
        i32("f44"),
        If(lambda s, ar: ar.ctx.get("plain_cstring_names", 0) == 0 and ver(ar) > 0xAA8, [obj("f38")], [cstr("f38")]),
    ])
    reg.provisional("moExtFeature_c", [
        base("moExtObjectInterface_c.FUN_4c179410"),
        Vgt(0x91, [obj("f50")]),
        Vin(0x9F9, 0x105E, [legacy("moExtFeature_c moExtFeatPatData_c 0x9fa-0x105d")]),
        Vge(0x11EB, [i32("f58")]),
    ])


def define(reg):
    define_surf_ids(reg)
    define_ent_refs(reg)
    define_chain_components(reg)
