from __future__ import annotations

from Dsl import Vgt, Vge, i32, u32, f64, cstr, base
from Schema import Rep
from defs.ResolvedCore import xo, obarray, concept_vt, vt, VIf

FOLDERS = (
    "moCommentsFolder_c", "moDocsFolder_c", "moInkMarkupFolder_c", "moFavoriteFolder_c",
    "moHistoryFolder_c", "moSelectionSetFolder_c", "moSensorFolder_c", "moMaterialFolder_c",
    "moEqnFolder_c", "moNotesAreaFtrFolder_c", "moSolidBodyFolder_c", "moSurfaceBodyFolder_c",
    "moDetailCabinet_c",
)


def define(reg):
    for c in FOLDERS:
        concept_vt(c)
    vt(0xA40, "moNotesAreaFtrFolder_c", True)
    reg.provisional("moNodeName_c", [cstr("f08")])
    for c in ("moCommentsFolder_c", "moDocsFolder_c", "moInkMarkupFolder_c"):
        reg.define(c, [base("moFolder_c")])
    reg.define("moFavoriteFolder_c", [
        base("moFolder_c"),
        Vgt(0x140D, [obarray("f3c8")]),
        Vgt(0x1C2F, [obarray("f3e8")]),
        Vgt(0x1C2F, [i32("f408")]),
    ])
    reg.define("moHistoryFolder_c", [
        base("moFolder_c"),
        Vgt(0x17E5, [obarray("f3c8")]),
    ])
    reg.define("moSelectionSetFolder_c", [
        base("moFolder_c"),
        Vgt(0x1BCB, [obarray("f3c0")]),
        Vgt(0x1BCF, [i32("f3e0")]),
    ])
    reg.define("moSensorFolder_c", [base("moFolder_c")])
    reg.define("moMaterialFolder_c", [
        base("moFolder_c"),
        Vgt(0x109E, [cstr("f378")]),
        Vge(0x1423, [u32("flags380")]),
    ])
    reg.define("moEqnFolder_c", [base("moFolder_c"), base("moFeature_c.FUN_4bb2b240")])
    reg.define("moFtrFolder_c", [
        base("moFolder_c"),
        xo("f388", "moFtrFolder_c"),
        i32("f37c"),
        Vgt(0xF61, [i32("f394")]),
        VIf(0xA40, [Vgt(0x23B9, [i32("f378")])]),
        Vgt(0x279B, [i32("f39c")]),
    ])
    reg.define("moNotesAreaFtrFolder_c", [base("moFtrFolder_c")])
    body = [
        base("moFolder_c"),
        Vgt(0xA38, [i32("f37c")]),
        Vge(0xA52, [i32("f380")]),
        Vgt(0x109E, [xo("f388", "moMaterialFolder_c")]),
        Vgt(0x23CA, [xo("f3d8", "moCutListSortOptions_c")]),
    ]
    reg.define("moSolidBodyFolder_c", body)
    reg.define("moSurfaceBodyFolder_c", body)
    reg.define("moDetailCabinet_c", [
        base("moModelFeature_c"),
        obarray("f368"),
        Vgt(0x218, [f64("f370"), f64("f378")]),
        Vgt(0x22C, [obarray("f388")]),
        Vgt(0x27B8, [
            i32("n3d8"),
            Rep("n3d8", "f3d8", [xo("o", "moDisplayImportedAnnotation_c")]),
        ]),
        Vgt(0x2B9A, [i32("f3f0")]),
    ])
