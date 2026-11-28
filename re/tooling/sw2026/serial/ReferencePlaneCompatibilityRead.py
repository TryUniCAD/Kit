from Core import Obj
from ReferencePlaneReadRules import case_axis, named, near, parameter_rows, plane_reference, require, transform, typed, vector
from ReferencePlaneSourcePlan import BASE_NAMES, BOSS, PLANE, SKETCH
from defs.ResolvedCore import isa


def project_face_offset(model, roots, archive_map, case, expected, snapshot):
    typed(model, "moPart_c")
    plane = named(roots, PLANE, "moRefPlane_c")
    support = named(roots, BASE_NAMES[case["base"]], "moRefPlane_c")
    profile = named(roots, SKETCH, "moProfileFeature_c")
    boss = named(roots, BOSS, "moExtrusion_c")
    data = typed(plane["f6f8"], "moFaceRefPlnData_c")
    wrapper = data["f90"]
    require(isinstance(wrapper, dict), "face-plane support wrapper must retain its embedded typed owner")
    reference = plane_reference(wrapper["f58"], model)
    display = typed(data["f98"], "moDisplayDistanceDim_c")
    handle, = [row["o"] for row in display["f850"]]
    typed(handle, "moFeatureDimHandle_c")
    dimension = typed(handle["ff0"], "ParallelPlaneDistanceDim_c")
    parameter = typed(dimension["f28"], "moLengthParameter_c")
    sketch_reference = plane_reference(profile["pd_f78"], model)
    depth_display = boss["f818"]["f18"]
    require(isinstance(depth_display, Obj) and isa(depth_display.cls, "moDisplayDim_c"),
            "source boss has no typed depth display")
    depth_handle, = [row["o"] for row in depth_display["f850"]]
    depth = depth_handle["ff0"]["f28"]["f58"]
    require(data["fa0"] in (0, 1), "face-plane dimension flip is outside the declared Boolean source input")
    checks = {
        "distance_matches_authored_input": near([parameter["f58"]], [expected["distance_m"]]),
        "distance_matches_native_api": near([parameter["f58"]], [snapshot["plane"]["distance_m"]]),
        "display_value_matches_parameter": near([display["fad0"]], [parameter["f58"]]),
        "flip_matches_authored_input": bool(data["fa0"]) is case["reverse"],
        "compatibility_mode_matches_factory": data["f5c"] == 5,
        "factory_argument_fa4": data["fa4"] == 1,
        "first_reference_index": data["fb4"] == 0,
        "optional_plane_data_reference_absent": data["has_fa8"] == 0,
        "selected_principal_datum": reference["datum_id"] == support["f08"] and reference["principal_kind"] == case_axis(case),
        "cached_origin_matches_input": near(vector(data["root"]), expected["plane_origin"]),
        "cached_normal_matches_input": near(vector(data["normal"]), expected["normal"]),
        "sketch_supports_actual_authored_plane": sketch_reference["datum_id"] == plane["f08"] and sketch_reference["principal_kind"] == 0,
        "boss_depth_matches_input": near([depth], [expected["depth_m"]]),
    }
    return {
        "plane_feature_id": plane["f08"], "plane_map_slot": plane.index,
        "support_feature_id": support["f08"], "profile_feature_id": profile["f08"], "boss_feature_id": boss["f08"],
        "wire_owner": data.cls, "data_map_slot": data.index, "reference": reference,
        "distance_m": parameter["f58"], "flip": bool(data["fa0"]), "reference_index": data["fb4"],
        "common_origin_m": vector(data["root"]), "common_normal": vector(data["normal"]),
        "common_transform": transform(data["f20"]), "border": [data[f"b{index}"] for index in range(4)],
        "mode_words": {key: data[key] for key in ("f50", "f54", "f58", "f5c", "f60", "f64", "fa0", "fa4", "has_fa8", "fb4")},
        "distance_graph": {"display": display.cls, "handle": handle.cls, "dimension": dimension.cls, "parameter": parameter.cls,
                           "display_map_slot": display.index, "handle_map_slot": handle.index, "dimension_map_slot": dimension.index,
                           "parameter_map_slot": parameter.index, "dimension_persistent_id": dimension["f50"],
                           "parameter_node_id": parameter["f08"], "parameter_name": parameter["f18"]["f08"]},
        "dimension_points": {key: vector(dimension[key]) for key in ("f80", "fa0", "fc0")},
        "dimension_axes_present": dimension["has_fe0"], "dimension_frame_present": dimension["has_ff0"],
        "sketch_reference": sketch_reference, "sketch_transform": transform(profile["pd_ff0"]),
        "boss_depth_m": depth, "native_parameters": parameter_rows(archive_map),
        "checks": checks, "passed": all(checks.values()),
        "construction_rule_source": "native Distance_c.CreateData, moFaceRefPlnData_c ctor/getters and existing shared serializer",
        "cache_formulas_and_neutral_states_qualified": False,
    }
