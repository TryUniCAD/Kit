from __future__ import annotations

from Dsl import cstr, emb, i32, obj, u16, u8
from Schema import If, Rep
from AnnotationWire import current_19000


def define(reg):
    reg.define(
        "moGTolDlgDataFrame_c",
        [
            current_19000(),
            cstr("f08"),
            u8("f28"),
            cstr("f30"),
            cstr("f38"),
            u8("f40"),
            cstr("f48"),
            cstr("f50"),
            emb("f58", "su_CStringArray"),
            emb("f80", "su_CStringArray"),
            emb("fa8", "su_CStringArray"),
            emb("fd0", "su_CStringArray"),
            emb("ff8", "su_CStringArray"),
            emb("f120", "su_CStringArray"),
            i32("f20"),
            i32("f24"),
            u16("f148"),
            obj("f10"),
            obj("f18"),
            If(
                lambda s, ar: s["f148"] != 0,
                [
                    emb("f150", "moGtolItemDatum2022_c"),
                    emb("f1c8", "moGtolItemDatum2022_c"),
                    emb("f240", "moGtolItemDatum2022_c"),
                ],
            ),
            i32("n2b8"),
            Rep(
                lambda s, ar: max(s["n2b8"], 0),
                "f2b8",
                [emb("e", "moGtolItemIndicator_c")],
            ),
        ],
    )
