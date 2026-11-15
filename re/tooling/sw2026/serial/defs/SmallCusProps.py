from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, i32, u32, u8, obj, cstr, rep, base, emb

PLANS = {
    "Contents/CusProps": ("rooted", 1),
}


def keyed(count, name):
    return [u32(count), rep(count, name, [i32("key"), obj("o")])]


def define(reg):
    reg.define("moCusPropMgr_c", [
        i32("f0c"),
        i32("f08"),
        *keyed("n20", "f20"),
        Vgt(0x42DD, [u8("f54")]),
    ])
    reg.define("moCusPropContainer_c", [
        obj("f08"),
        obj("f10"),
        Vgt(0x278C, [obj("f18")]),
        Vge(0x279F, [i32("f20")]),
    ])
    reg.define("moFilePropContainer_c", [obj("f08"), obj("f10")])
    reg.define("moAdvCusPropList_c", [base("suObList")])
    reg.define("moAdvCusProp_c", [
        emb("f10", "suObList"),
        i32("f08"),
        i32("f0c"),
        cstr("f58"),
        Vlt(0x2791, [cstr("type_name")], [i32("f7c")]),
        cstr("f60"),
        cstr("f70"),
        i32("f78"),
        Vgt(0x27A2, [i32("f80")]),
        Vge(0x27D9, [i32("f84")]),
    ])
    reg.define("moCutListPropContainer_c", [
        *keyed("n08", "f08"),
        Vgt(0x2B62, [*keyed("n38", "f38")]),
    ])
