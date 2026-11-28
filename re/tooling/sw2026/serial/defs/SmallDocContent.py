from __future__ import annotations

from Dsl import i32, u32, f64, obj, cstr, time32, rep, emb
from Schema import If

PLANS = {
    "SwDocContentMgr/SwDocContentMgrInfo": ("rooted", 1),
}


def pos(name):
    return lambda s, ar: max(0, s[name])


def keyed(count, name, value):
    return [u32(count), rep(count, name, [cstr("k"), value("v")])]


def nested(count, name, items):
    return [
        i32(count),
        rep(pos(count), name, [
            cstr("k"),
            i32("n"),
            If(lambda s, ar: s["n"] > 0, [u32("m"), rep("m", "items", items)]),
        ]),
    ]


def define(reg):
    reg.define("moBCModeInfo_c", [
        cstr("f08"),
        time32("f10"),
        cstr("f28"),
        i32("f30"),
        emb("f38", "suObList"),
        *keyed("n40", "f40", cstr),
        *keyed("n50", "f50", cstr),
        *keyed("n60", "f60", i32),
        cstr("fb0"),
        obj("fb8"),
        time32("f18"),
        *keyed("nc0", "fc0", cstr),
        i32("ff4"),
        i32("ff8"),
        i32("ffc"),
        *nested("nd0", "fd0", [i32("k"), cstr("v")]),
        *nested("ne0", "fe0", [i32("a"), i32("b")]),
        u32("f20"),
        *keyed("n70", "f70", i32),
        *keyed("n80", "f80", f64),
        *keyed("n90", "f90", i32),
        *keyed("na0", "fa0", i32),
    ])
