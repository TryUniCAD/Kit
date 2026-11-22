from io import BytesIO
from math import isclose, radians

from ThinHeldoutPacket import require


def vector(value):
    return (value.x, value.y, value.z)


def close(actual, expected):
    return isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)


def tuple_close(actual, expected):
    return all(close(a, b) for a, b in zip(actual, expected, strict=True))


def check_projection(document, case, include_brep):
    from BuildThinPlanes import WALL_MODES
    from RevolveFamilyModel import thin_predictions, world
    from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
    from interchange.Features.Revolves.ThinRevolve import ThinRevolve

    document.assert_valid()
    require(document.metadata.get("solidworks.typed_thin_revolve_semantics") is True
            and not document.brep_payloads and bool(document.brep) == include_brep,
            "cold strict read did not qualify a model-only thin feature")
    (feature,) = [row for row in document.feature_timeline if isinstance(row.definition, ThinRevolve)]
    definition = feature.definition
    require(definition.WallMode == WALL_MODES[case["wall_mode"]]
            and feature.kind == FeatureKind.KRevolution and feature.operation == BooleanOp.KCreate,
            "cold reader changed the live thin sweep or wall mode")
    sweep = definition.SweepValue
    params = {row.id: row for row in document.parameters}
    ids = (sweep.AlongParameterId, *definition.GetWallIds())
    values = [radians(case["angle_deg"]), *(1000 * v for v in case["wall_m"] if v > 0.0)]
    names = ("D1", "D3", "D4")[:len(ids)]
    require(ids == feature.parameter_ids and len(params) == len(ids), "cold reader lost the complete editable driver inventory")
    for index, (key, name, expected) in enumerate(zip(ids, names, values, strict=True)):
        actual = params[key]
        require(actual.name == name and actual.owner_id == feature.id and actual.provenance
                and actual.expression is None and actual.value.unit == ("mm" if index else "rad")
                and close(actual.value.value, expected), "cold reader changed a live actual driver")
    (sketch,) = document.sketches
    (support,) = [row for row in document.support_planes if row.id == sketch.support_plane_id]
    expected_frame = [world(case, point) for point in ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))]
    frame = support.transform
    require([vector(v) for v in (frame.origin, frame.x_axis, frame.y_axis, frame.z_axis)] == expected_frame,
            "cold reader changed the signed principal frame")
    (line, axis) = sketch.entities
    require(feature.sketch_id == sketch.id and not sketch.closed_profile_entity_ids and not sketch.constraints
            and not line.construction and axis.construction, "cold reader lost open profile and centreline roles")
    for entity, radial, levels in ((line, case["axis_x_m"] + case["profile_radius_m"], case["axial_m"]),
                                    (axis, case["axis_x_m"], case["axis_axial_m"])):
        require(tuple_close((entity.geometry.start.x, entity.geometry.start.y, entity.geometry.end.x, entity.geometry.end.y),
                            (1000 * radial, 1000 * levels[0], 1000 * radial, 1000 * levels[1])),
                "cold reader changed actual local line incidence")
    (selection,) = [row for row in document.selections if row.id == sweep.AxisSelectionId]
    require(feature.selection_ids == (selection.id,)
            and tuple((row.entity_kind, row.entity_id) for row in selection.path)
            == (("sketch", sketch.id), ("sketch_entity", axis.id))
            and tuple_close(vector(sweep.AxisOrigin), world(case, (1000 * case["axis_x_m"], 1000 * case["axis_axial_m"][0], 0)))
            and vector(sweep.AxisDirection) == world(case, (0, 1, 0))
            and sweep.SideMode == "one_sided" and sweep.AgainstParameterId is None,
            "cold reader changed selected axis ownership or forward angular end")
    (body,) = document.bodies
    require(body.final_feature_id == feature.id and body.name == feature.name and body.provenance,
            "cold reader lost actual thin body name and creator")
    (config,) = document.configurations
    require(config.active and config.name == "Default", "cold reader lost the actual active configuration")
    if include_brep:
        shape = document.brep
        require(not shape.validate(frozenset((body.id,))) and len(shape.bodies) == 1,
                "cold analytic thin body has invalid topology")
        actual = body.topology
        prediction = next(row for sign, row in thin_predictions(dict(case, first_wall_sign=1))
                          if sign in (None, 1))
        require(actual.solid_count == actual.shell_count == 1
                and (actual.face_count, actual.edge_count, actual.vertex_count) == (6, 12, 8)
                and close(actual.volume, prediction["volume_m3"] * 1e9)
                and close(actual.surface_area, prediction["area_m2"] * 1e6)
                and tuple_close((*vector(actual.bounding_box.minimum), *vector(actual.bounding_box.maximum)),
                                [1000 * n for n in prediction["bounds_m"]]),
                "cold analytic thin solid differs from independent neutral sector")
    return {"driver_count": len(ids), "strict_typed_thin": True, "analytic_body": include_brep,
            "actual_body_creator": True}


def read_cold(raw, case, sdk):
    from AuditPrincipalReader import make_guard
    from convert import open_document

    state, audit = make_guard(sdk)
    state["enabled"] = True
    checks = {}
    try:
        for label, include_brep in (("model_only", False), ("analytic_brep", True)):
            model = open_document(BytesIO(raw), source_format="solidworks.sldprt", strict=True,
                                  include_brep=include_brep, include_tessellation=False)
            checks[label] = check_projection(model, case, include_brep)
    finally:
        state["enabled"] = False
    require(not audit["unexpected_attempts"], "strict thin reader took an unexpected runtime input")
    return {"checks": checks, "unexpected_runtime_reads": 0, "package_layout_reads": audit["grammar_reads"]}
