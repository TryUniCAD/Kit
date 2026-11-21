from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, ver, i32, u32, u16, u8, emb, base, count
from Schema import If, Rep, Raw
from defs.ResolvedCore import xo, obarray, concept_vt, Cnd, Ctx, NCtx, Legacy, PARENT, has_condition


def flag(name):
    return lambda s, ar: s[name] != 0


def signed_count(name):
    return lambda s, ar: max(s[name], 0)


def cond20_cond1(s, ar):
    return not has_condition(ar, 0x20) and has_condition(ar, 1)


def body_raw_skip(s, ar):
    return s["len"] == 1 or bool(s.get("param6", 0))


def define(reg):
    for c in ("moProfileFeature_c", "moOriginProfileFeature_c"):
        concept_vt(c)
    PARENT["moProfileFeature_c"] = "moModelFeature_c"
    PARENT["moOriginProfileFeature_c"] = "moProfileFeature_c"
    reg.define("mo_loadBodyFromArchiveRaw", [
        If(lambda s, ar: ver(ar) > 0xC9B and not ar.ctx.get("compressed_stream", 0), [
            i32("len"),
            If(body_raw_skip, [Raw("skipped", lambda s, ar: s["len"])], [
                Vgt(0x811, [u8("kernel")]),
                Raw("parasolid", lambda s, ar: s["len"] - (1 if ver(ar) > 0x811 else 0)),
            ]),
        ], [
            Legacy("mo_loadBodyFromArchiveRaw without length prefix"),
        ]),
    ])
    reg.define("mo_loadBodyFromArchive", [
        Vgt(0x1E0, [u8("empty")]),
        If(lambda s, ar: s.get("empty", 0) == 0, [
            Vlt(0xA89, [Legacy("mo_loadBodyFromArchiveRaw pre-0xa89")], [
                Ctx("model_compressed_stream", [], [
                    base("mo_loadBodyFromArchiveRaw"),
                ]),
            ]),
        ]),
    ])
    reg.define("FUN_4bb09f20", [
        u32("elem"),
        If(flag("elem"), [
            u32("grow"),
            u32("kind"),
            u32("n"),
            Raw("data", lambda s, ar: s["n"] * s["elem"]),
        ]),
    ])
    reg.define("moProfileData.FUN_4bb2d5c0", [
        Vlt(0xB7D, [Legacy("FUN_4bb2d5c0 pre-0xb7d")], [
            Vgt(0xB89, [
                u32("f2b0"),
                i32("n2a8"),
                Rep(signed_count("n2a8"), "f2a8", [xo("chain", "moSketchChain_c")]),
            ]),
        ]),
    ])
    reg.define("moProfileData.FUN_4bb2ca30", [
        Vlt(0x903, [Legacy("FUN_4bb2ca30 pre-0x903")]),
        i32("f10"),
        Cnd(0x6000, [], [
            NCtx("ctx874", [
                Cnd(0x40000, [
                    i32("transfer"),
                    If(flag("transfer"), [i32("transfer_ptr")]),
                ]),
                If(lambda s, ar: not s.get("transfer", 0), [emb("f198", "mo_loadBodyFromArchive")]),
            ]),
        ]),
        Vgt(0x99B, [
            i32("n238"),
            Rep(signed_count("n238"), "f238", [u32("k"), u32("v")]),
        ]),
        Vlt(0xC75, [Legacy("FUN_4bb2ca30 pre-0xc75")]),
        obarray("f168"),
        emb("f188", "FUN_4bb09f20"),
        If(lambda s, ar: ver(ar) > 0x992 and s.get("f198", {}).get("empty", 1) == 0, [
            i32("n208"),
            Rep(signed_count("n208"), "f208", [i32("k"), emb("body", "mo_loadBodyFromArchive")]),
        ]),
    ])
    reg.define("moProfileFeature_c.FUN_4bb2d1d0", [
        Vgt(0x84B, [
            u32("f3e0"),
            emb("f3e8", "moProfileFeature_c.contours"),
        ]),
    ])
    reg.define("moProfileFeature_c.contours", [
        count("n"),
        Rep("n", "items", [
            xo("contour", "moOneContour_c"),
            u16("m"),
            Rep("m", "ids", [u32("v")]),
        ]),
    ])
    reg.define("moProfileFeature_c", [
        base("moModelFeature_c"),
        Vgt(0x944, [i32("f390")]),
        Vgt(0xA9B, [xo("orig_dim_feature", "suObList")]),
        Vgt(0x844, [i32("f3dc")]),
        If(flag("f3dc"), [
            xo("reused_from", "moProfileFeature_c"),
            xo("f388", "moContourChooser_c"),
            u16("f3c0"),
            xo("f3b8", "sgLineHandle"),
            Vlt(0x85E, [Legacy("reused profile pre-0x85e")]),
            Vlt(0xB7D, [Legacy("reused profile pre-0xb7d")]),
            base("moProfileFeature_c.FUN_4bb2d1d0"),
        ], [
            Cnd(0x20, [Legacy("moProfileFeature_c condition 0x20 block")]),
            xo("pd_f80", "sgSketch"),
            If(lambda s, ar: ver(ar) < 0xB7D or ver(ar) > 0xB89, [emb("d5c0", "moProfileData.FUN_4bb2d5c0")]),
            emb("ca30", "moProfileData.FUN_4bb2ca30"),
            Vlt(0xB7D, [Legacy("FUN_4bb2da00 pre-0xb7d")]),
            base("moProfileFeature_c.FUN_4bb2d1d0"),
            xo("f3b8", "sgLineHandle"),
            If(cond20_cond1, [u16("write_ref")]),
            If(lambda s, ar: s.get("write_ref", 1) == 0, [
                If(cond20_cond1, [
                    emb("pd_ff0", "mgXform_c.restore"),
                    u16("pd_has_fe8"),
                    If(flag("pd_has_fe8"), [emb("pd_fe8", "mgXform_c.restore")]),
                ]),
            ], [
                xo("pd_f78"),
                Vgt(0x9A, [
                    emb("pd_ff0", "mgXform_c.restore"),
                    Vgt(0x154, [u16("pd_has_fe8")]),
                    If(lambda s, ar: (s["pd_has_fe8"] if ver(ar) > 0x154 else int(ver(ar) > 0x142)) != 0, [
                        emb("pd_fe8", "mgXform_c.restore"),
                    ]),
                ]),
            ]),
            Vlt(0x5A, [Legacy("profile f100 pre-0x5a")], [u16("pd_f100")]),
            Vgt(0x14E, [xo("pd_f110")]),
            Vgt(0x1D6, [i32("pd_f11c")]),
            Vgt(0x206, [i32("pd_f118")]),
            Vgt(0x714, [Vlt(0x770, [xo("old_bitmap", "moSketchBitmap_c")])]),
            Vge(0x72A, [u32("pd_f2a0")]),
            Vge(0x7E4, [u16("f3c0")]),
            Vgt(0x80B, [xo("f388", "moContourChooser_c")]),
            Vgt(0x868, [obarray("pd_f128"), obarray("pd_f148")]),
            Vgt(0x80F, [Vlt(0x95F, [Legacy("profile user objects 0x810-0x95e")])]),
            Vge(0x2B92, [i32("f42c")]),
        ]),
    ])
    reg.define("moOriginProfileFeature_c", [base("moProfileFeature_c")])
