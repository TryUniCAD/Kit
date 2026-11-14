from __future__ import annotations

from Dsl import Vgt, Vlt, Fnz, i32, u32, u16, obj, cstr, time32, base, rep, emb
from Schema import Cnt


def define(reg):
    reg.define("moStamp_c", [u16("f08"), u16("f0c"), u16("f10"), time32("f18"), cstr("f20")])
    reg.define("moLogs_c", [base("suObList"), i32("f48"), cstr("f50")])
    reg.define("moHeader_c", [
        Vgt(0x371B, [i32("fec")]),
        obj("f10"),
        obj("f18"),
        obj("f20"),
        Vgt(0xF0, [time32("f50")]),
        i32("f08"),
        obj("f30"),
        Vgt(0x96, [u32("f40")]),
        Vgt(0xD8, [obj("f38")]),
        Vgt(0x30B, [u32("f44")]),
        Vgt(0x4E4, [i32("f58")]),
        Vgt(0x500, [i32("f68")]),
        Vgt(0x505, [time32("f70")]),
        Vgt(0x530, [i32("f60")]),
        Vgt(0x859, [i32("f78")]),
        Vgt(0x91E, [i32("fc0")]),
        Vgt(0xAA1, [obj("f28")]),
        Vgt(0xB8C, [i32("fc4")]),
        Vgt(0xCF6, [u32("f7c")]),
        Vgt(0xE5C, [time32("f48")]),
        Vgt(0xF3A, [obj("f88")]),
        Vgt(0x128F, [i32("fc8")]),
        Vgt(0x1303, [
            i32("f64"),
            Vgt(0x130E, [i32("bboxflag"), Fnz("bboxflag", [emb("bbox", "mgBBox_c.restore")])]),
            Vgt(0x2783, [i32("fcc"), i32("fd0"), i32("fd4")]),
            Vgt(0x2BC2, [u32("f80")]),
            Vgt(0x2FA3, [i32("f9c"), i32("fa0"), i32("fa4"), i32("fa8"), i32("fac"), i32("fb0")]),
            Vgt(0x336F, [i32("fe8")]),
            Vgt(0x3B0A, [i32("ff0"), i32("ff4"), i32("ff8"), i32("ffc"), i32("f100"), i32("f104")]),
            Vgt(0x3B1F, [i32("f108")]),
            Vgt(0x3DB8, [i32("f10c")]),
            Vgt(0x3F01, [i32("f98")]),
        ]),
    ])
