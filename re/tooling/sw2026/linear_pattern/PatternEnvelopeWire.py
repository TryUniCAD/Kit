from Dsl import base, emb, f64, i32, u8
from Schema import Fn
from defs.ResolvedCore import PARENT, xo


SCHEMAS = {
    "moPlaneInterAxisData_c": [
        base("moRefAxisData_c"), xo("f80", "moPlaneRef_w"), xo("f88", "moPlaneRef_w"),
    ],
    "moConstraintCoincLineAtAnglePlaneRefplaneData_c": [
        base("moConstraintRefplaneData_c.FUN_4b8e2ac0"), i32("f148"),
        xo("f150", "moDisplayAngularDim_c"),
    ],
    "moConstraintRefplaneData_c": [base("moConstraintRefplaneData_c.FUN_4b8e2ac0")],
    "moRefPlaneAngleGeom_c": [
        base("moRefPlaneGeometry_c.FUN_4c2d8b90"), f64("f38"), u8("f40"),
    ],
    "moRefAtAngleData_c": [
        base("moRefPlnData_c.serializePlaneData"), emb("f90", "moPlaneRef_w"),
        xo("f98", "moLineRef_w"), xo("fa0", "moDisplayAngularDim_c"),
        i32("fa8"), i32("fac"), i32("fb0"), i32("fb4"),
    ],
}
BASES = {
    "moPlaneInterAxisData_c": "moRefAxisData_c",
    "moConstraintCoincLineAtAnglePlaneRefplaneData_c": "moConstraintRefplaneData_c",
    "moRefPlaneAngleGeom_c": "moRefPlaneGeometry_c",
    "moRefAtAngleData_c": "moRefPlnData_c",
}


def read_context(ar, scope, owner):
    if ar.version != 19000 or ar.ctx.get("conditions", 0) != 0 or not ar.ctx.get("model_is_part"):
        raise ValueError("oblique direction audit requires ordinary version-19000 part context")


def add_envelope_rules(registry):
    for name, rules in SCHEMAS.items():
        if registry.has(name):
            raise ValueError("existing schema must be reviewed before the angle observation: " + name)
        registry.provisional(name, [Fn(read_context, read_context), *rules])
    for derived, base_name in BASES.items():
        previous = PARENT.setdefault(derived, base_name)
        if previous != base_name:
            raise ValueError("oblique direction class hierarchy differs " + derived)
    return registry
