from __future__ import annotations

from Dsl import emb, f64, u8, u32
from Schema import If, Rep


def restore_kind(scope, archive, kind):
    return (scope["f78"] & 0xF0) == kind


def operator_kind(scope, archive, kind):
    return (scope["words"][28]["w"] & 0xF0) == kind


def define(reg):
    reg.define("mgMatrix_c.restore", [f64(f"m{index}") for index in range(9)])
    for name in (
        "mgPoint_c.operator>>", "mgPoint_c.restore", "mgVector_c.restore",
    ):
        reg.define(name, [f64("x"), f64("y"), f64("z")])
    reg.define("mgPoint_c.restore2D", [f64("x"), f64("y")])
    reg.define("mgXform_c.restore", [
        u8("has_matrix"),
        If(lambda scope, archive: scope["has_matrix"] != 0, [emb("f08", "mgMatrix_c.restore")]),
        f64("f58"), f64("f60"), f64("f68"), f64("f70"), u8("f78"),
        If(lambda scope, archive: restore_kind(scope, archive, 0x40), [emb("f80", "mgMatrix5_c.restore")]),
        If(lambda scope, archive: restore_kind(scope, archive, 0x20), [emb("f80", "mgPerspInfo_c.restore")]),
        If(lambda scope, archive: restore_kind(scope, archive, 0x10), [emb("f80", "mgPerspInfoBase_c.restore")]),
    ])
    reg.define("mgXform_c.operator>>", [
        Rep(lambda scope, archive: 30, "words", [u32("w")]),
        If(lambda scope, archive: operator_kind(scope, archive, 0x10), [emb("persp", "mgPerspInfoBase_c.restore")]),
        If(lambda scope, archive: operator_kind(scope, archive, 0x20), [emb("persp", "mgPerspInfo_c.restore")]),
        If(lambda scope, archive: operator_kind(scope, archive, 0x40), [emb("persp", "mgMatrix5_c.restore")]),
    ])
