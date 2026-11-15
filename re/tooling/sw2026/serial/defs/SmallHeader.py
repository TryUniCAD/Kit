from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, i32, u32, obj, cstr, time32, rep, emb

PLANS = {
    "Contents/CMgrHdr2": ("rooted", 1),
}


def define(reg):
    reg.define("dmConfigHeader_c", [
        i32("f08"),
        cstr("f10"),
        i32("f30"),
        Vgt(0x53C, [u32("f38")]),
        Vgt(0x7F4, [cstr("f18"), i32("f34")]),
        Vgt(0x857, [i32("f40")]),
        Vgt(0xA31, [cstr("f20"), cstr("f28")]),
        Vgt(0xF57, [i32("f44")]),
        Vgt(0x2B85, [i32("f48")]),
        Vgt(0x2F7A, [u32("f50")]),
        Vge(0x2FB8, [u32("f4c")]),
    ])
    reg.define("dmConfigMgrHeader_c", [
        emb("f08", "suObList"),
        Vgt(0xBD3, [Vlt(0xCFF, [i32("n58"), rep("n58", "f58", [obj("o")])])]),
        Vgt(0xFD1, [time32("f60")]),
        Vgt(0x27D5, [i32("f68")]),
    ])
