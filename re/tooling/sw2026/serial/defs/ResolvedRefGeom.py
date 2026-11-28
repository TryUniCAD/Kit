from __future__ import annotations

from Dsl import Vgt, Vge, Vlt, ver, i32, u16, u8, f64, emb, base
from Schema import If
from defs.ResolvedCore import xo, concept_vt, Legacy, PARENT

PLANE = "moRefPlnData_c.serializePlaneData"


def flag(name):
    return lambda s, ar: s[name] != 0


def define(reg):
    for c, p in (("moAbsoluteRefPlnData_c", "moRefPlnData_c"), ("moFixedRefPlnData_c", "moAbsoluteRefPlnData_c"),
                 ("moFaceRefPlnData_c", "moRefPlnData_c"), ("moFacePtRefPlnData_c", "moRefPlnData_c"),
                 ("moLinePtBaseData_c", "moRefPlnData_c"), ("moLinePtRefPlnData_c", "moLinePtBaseData_c"),
                 ("moConstraintRefplaneData_c", "moRefPlnData_c"),
                 ("moConstraintMidPlaneRefplaneData_c", "moConstraintRefplaneData_c"),
                 ("moConstraintPerpPlnTanOneCylinderRefplaneData_c", "moConstraintRefplaneData_c"),
                 ("moConstraintPrllPlnTanOneCylinderRefplaneData_c", "moConstraintRefplaneData_c"),
                 ("moConstraintLineAtAnglePlaneRefplaneData_c", "moConstraintRefplaneData_c"),
                 ("moConstraintCoincLineParallelPlaneRefplaneData_c", "moConstraintLineAtAnglePlaneRefplaneData_c"),
                 ("moConstraintCoincOrProjLinePerpPlaneRefplaneData_c", "moConstraintLineAtAnglePlaneRefplaneData_c"),
                 ("moConstraintCoincLinePerpPlaneRefplaneData_c", "moConstraintCoincOrProjLinePerpPlaneRefplaneData_c"),
                 ("moRefAxis_c", "moRefGeom_c"), ("moSurfaceAxisData_c", "moRefAxisData_c")):
        PARENT[c] = p
    concept_vt("moRefAxis_c")
    for c in ("moAbsoluteRefPlnData_c", "moFixedRefPlnData_c"):
        reg.define(c, [base(PLANE)])
    reg.define("moFaceRefPlnData_c", [
        base(PLANE),
        Vlt(0x14A, [Legacy("moFaceRefPlnData_c plane data pre-0x14a")]),
        emb("f90", "moPlaneRef_w"),
        xo("f98", "moDisplayDim_c"),
        i32("fa0"),
        Vgt(0xB3B, [i32("fa4")]),
        Vgt(0xB6E, [
            i32("has_fa8"),
            If(flag("has_fa8"), [emb("fa8", "moPlaneDataRef_w")]),
        ]),
        Vge(0x10D5, [i32("fb4")]),
    ])
    reg.define("moFacePtRefPlnData_c", [
        base(PLANE),
        Vlt(0x51, [Legacy("moFacePtRefPlnData_c vertex pre-0x51")], [xo("f88", "moPointRef_w")]),
        emb("f90", "moPlaneRef_w"),
        Vgt(0x10D4, [i32("f98"), i32("f9c")]),
        Vlt(0x14A, [Legacy("moFacePtRefPlnData_c plane data pre-0x14a")]),
    ])
    reg.define("moLinePtRefPlnData_c", [
        base(PLANE),
        Vlt(0x51, [Legacy("moLinePtRefPlnData_c vertex pre-0x51")], [xo("f88", "moPointRef_w")]),
        Vlt(0xC3, [Legacy("moLinePtRefPlnData_c curve pre-0xc3")], [xo("f90", "moCurveRef_w")]),
        Vgt(0x10D4, [i32("f98"), i32("f9c")]),
        Vlt(0x14A, [Legacy("moLinePtRefPlnData_c plane data pre-0x14a")]),
    ])
    PARENT["moPerLinePtRefPlnData_c"] = "moLinePtRefPlnData_c"
    PARENT["moTwoPtsAxisData_c"] = "moRefAxisData_c"
    reg.define("moPerLinePtRefPlnData_c", [
        base("moLinePtRefPlnData_c"),
        Vlt(0x13B, [Legacy("moPerLinePtRefPlnData_c fa0 pre-0x13b")], [u16("fa0")]),
        Vge(0x982, [i32("fa4")]),
    ])
    reg.define("moTwoPtsAxisData_c", [
        base("moRefAxisData_c"),
        Vgt(0x50, [xo("f80", "moPointRef_w"), xo("f88", "moPointRef_w")], [Legacy("moTwoPtsAxisData_c vertices pre-0x51")]),
    ])
    reg.define("moConstraintRefplaneInterfaceData_c", [
        xo("f08", "moRefPlaneGeometry_c"),
        xo("f10", "moRefPlaneGeometry_c"),
        xo("f18", "moRefPlaneGeometry_c"),
    ])
    reg.define("moConstraintRefplaneData_c.FUN_4b8e2ac0", [
        base(PLANE),
        xo("f88", "moConstraintRefplaneInterfaceData_c"),
    ])
    for c in ("moConstraintMidPlaneRefplaneData_c", "moConstraintCoincLineParallelPlaneRefplaneData_c",
              "moConstraintPerpPlnTanOneCylinderRefplaneData_c", "moConstraintPrllPlnTanOneCylinderRefplaneData_c"):
        reg.define(c, [base("moConstraintRefplaneData_c.FUN_4b8e2ac0")])
    for c in ("moConstraintCoincLinePerpPlaneRefplaneData_c", "moConstraintCoincCurveRefplaneData_c"):
        reg.define(c, [base("moConstraintRefplaneData_c.FUN_4b8e2ac0"), i32("fe8")])
    reg.define("moRefPlaneGeometry_c.FUN_4c2d8b90", [
        xo("f08", "moRefWrapper_c"),
        f64("u"),
        f64("v"),
        emb("f20", "mgPoint_c.restore"),
    ])
    for c in ("moRefPlaneCoincidentGeom_c", "moRefPlaneParallelGeom_c"):
        PARENT[c] = "moRefPlaneGeometry_c"
        reg.define(c, [base("moRefPlaneGeometry_c.FUN_4c2d8b90")])
    for c in ("moRefPlanePerpendicularGeom_c", "moRefPlaneMidPlaneGeom_c", "moRefPlaneTangentGeom_c"):
        PARENT[c] = "moRefPlaneGeometry_c"
        reg.define(c, [base("moRefPlaneGeometry_c.FUN_4c2d8b90"), u8("f38")])
    reg.define("moRefAxisData_c", [
        If(lambda s, ar: ver(ar) < 0x89 or ver(ar) > 0x92, [
            emb("f18", "mgPoint_c.restore"),
            emb("f30", "mgPoint_c.restore"),
        ]),
        Vlt(0x256, [], [f64("f08"), f64("f10")]),
        Vgt(0x646, [emb("f50", "mgVector_c.restore")]),
        Vge(0x808, [emb("f68", "mgPoint_c.restore")]),
    ])
    reg.define("moSurfaceAxisData_c", [
        base("moRefAxisData_c"),
        xo("f80", "moSurfaceRef_w"),
    ])
    reg.define("moRefAxis_c", [
        base("moRefGeom_c"),
        Vgt(0x88, [xo("f700", "moRefAxisData_c")]),
    ])
