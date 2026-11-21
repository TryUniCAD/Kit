from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, i32, u16, u8, f64, obj, cstr, time32, emb, base


def define(reg):
    reg.define("moCStringHandle_c", [cstr("f08")])
    reg.define("moReferencedConfiguration_c", [cstr("f08"), i32("f10")])
    reg.define("moSharedFileDef_c", [
        Vlt(0xFA7, [cstr("f18"), cstr("f10")], [obj("h18"), obj("h10")]),
        u16("f20"),
        u8("f08"),
        time32("f28"),
        Vgt(0x1427, [Vlt(0x146C, [u8("f34")])]),
        Vgt(0x1FB3, [cstr("f38")]),
        Vgt(0x23D9, [cstr("f40")]),
        Vgt(0x2F82, [cstr("f50")]),
        Vge(0x3330, [u8("f35")]),
    ])
    reg.define("moExtObject_c", [
        Vlt(0xF18, [obj("legacy"), i32("legacy_l")], [
            emb("shared", "moSharedFileDef_c"),
            u8("f58"),
            time32("f60"),
        ]),
        Vlt(0x45, [u16("old45")]),
        Vlt(0xF18, [u16("old_type")]),
        Vgt(0x62, [i32("f48")]),
        Vgt(0x6C, [i32("f4c")]),
        Vgt(0x8DD, [i32("f78"), emb("refcfg", "moReferencedConfiguration_c")]),
        Vgt(0xAD0, [i32("f54")]),
        Vgt(0xD95, [Vlt(0xF18, [i32("old_d95")])]),
        Vge(0xFD2, [time32("f70")]),
        Vgt(0x3F12, [i32("f50")]),
    ])
    reg.define("mgBBox_c.restore", [f64(f"b{k}") for k in range(10)])
    reg.define("moExtObjectList_c", [base("suObList")])
