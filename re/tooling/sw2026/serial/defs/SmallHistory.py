from __future__ import annotations

from Dsl import i32, u32, u16, obj, cstr, rep, emb
from Schema import If

PLANS = {
    "_MO_VERSION_19000/Biography": ("rooted", 1),
    "_MO_VERSION_19000/History": ("rooted", 1),
}


def flat(ar):
    return ar.ctx.get("force_flat", 0) != 0


def last_version(s):
    states = s["states"]
    return states[-1]["st"]["f30"]


def Last(n, then):
    return If(lambda s, ar: last_version(s) > n, then)


def triple(k):
    return [cstr(f"s{k}"), i32(f"l{k}"), u32(f"a{k}"), u32(f"b{k}")]


def define(reg):
    reg.define("moStartEndRecord_c", [
        u32("f08"), u32("f0c"), u32("f10"),
        *[op for k in range(6) for op in triple(k)],
    ])
    reg.define("moBiographyRecord_c", [
        u32("f08"),
        i32("f0c"),
        i32("f10"),
        u32("f14"), u32("f18"), u32("f1c"), u32("f20"), u32("f24"), u32("f28"),
        cstr("f30"),
        u16("f38"),
        emb("f40", "moStartEndRecord_c"),
        emb("fe8", "moStartEndRecord_c"),
    ])
    reg.define("moBiography_c", [
        i32("n"),
        rep("n", "records", [emb("r", "moBiographyRecord_c")]),
    ])
    reg.define("moDateCodeState_c", [i32("f08")])
    reg.define("moDateCodeHistory_c", [
        i32("n"),
        rep("n", "states", [emb("st", "moDateCodeState_c")]),
    ])
    reg.define("moVersionState_c", [
        emb("f08", "moStamp_c"),
        u32("f30"),
        If(lambda s, ar: s["f30"] < 0x178,
           [If(lambda s, ar: s["f30"] >= 0x175, [i32("datecode")])],
           [obj("f38")]),
    ])
    reg.define("moVersionHistory_c", [
        i32("n"),
        rep("n", "states", [emb("st", "moVersionState_c")]),
        If(lambda s, ar: not flat(ar), [
            Last(0x318, [i32("f28"), u32("f2c")]),
            If(lambda s, ar: not flat(ar), [Last(0x45B, [i32("f30")])]),
        ]),
        Last(0x46B, [u16("f38"), i32("f3c"), i32("f40")]),
    ])
