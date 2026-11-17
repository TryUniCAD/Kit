from math import isclose, isfinite

from Core import ArchiveError, Obj
from Dsl import base, f64, i32, u8
from Schema import Fn
from defs.ResolvedCore import PARENT, isa


VERSION = 19000
NEW_CLASSES = ("moRefPlaneDistanceGeom_c", "moConstraintRefplaneData_c")
MODEL_SHA256 = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
SERIALIZERS = {
    "moRefPlaneDistanceGeom_c": "0x4c2d8ae0",
    "moConstraintRefplaneData_c": "0x4b8e2ac0",
}


def require(value, message):
    if not value:
        raise ArchiveError(message)


def ordinary_context(archive, scope, owner):
    require(archive.version == VERSION and archive.ctx.get("conditions", 0) == 0,
            "offset-plane source rules require ordinary version-19000 serialization")


def define_offset(registry):
    require(not any(registry.has(name) for name in NEW_CLASSES),
            "offset-plane audit must not replace an existing class schema")
    PARENT["moRefPlaneDistanceGeom_c"] = "moRefPlaneGeometry_c"
    registry.provisional("moRefPlaneDistanceGeom_c", [
        Fn(ordinary_context, ordinary_context),
        base("moRefPlaneGeometry_c.FUN_4c2d8b90"),
        f64("f38"), u8("f40"), i32("f44"),
    ])
    registry.provisional("moConstraintRefplaneData_c", [
        Fn(ordinary_context, ordinary_context),
        base("moConstraintRefplaneData_c.FUN_4b8e2ac0"),
    ])
    return registry


def typed(value, name):
    require(isinstance(value, Obj) and value.cls == name, f"expected typed {name}")
    return value


def vector(value):
    result = [value[axis] for axis in ("x", "y", "z")]
    require(all(type(number) in (float, int) and isfinite(number) for number in result),
            "plane source contains a nonfinite vector")
    return result


def near(left, right):
    return len(left) == len(right) and all(
        isclose(first, second, rel_tol=1e-12, abs_tol=1e-12)
        for first, second in zip(left, right, strict=True)
    )


def transform(value):
    require(value["has_matrix"] in (0, 1), "source plane has an invalid matrix flag")
    matrix = [value["f08"][f"m{index}"] for index in range(9)] if value["has_matrix"] else [
        1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0,
    ]
    translation = [value[key] for key in ("f58", "f60", "f68")]
    require(all(isfinite(number) for number in (*matrix, *translation, value["f70"])),
            "source plane has a nonfinite stored transform")
    return {"has_matrix": value["has_matrix"], "matrix": matrix, "translation": translation,
            "scale": value["f70"], "flags": value["f78"]}


def named(roots, name, class_name):
    matches = [node for node in roots if isinstance(node, Obj) and node.cls == class_name and
               isinstance(node.get("f18"), Obj) and node["f18"].get("f08") == name]
    require(len(matches) == 1, f"expected one named source {class_name}")
    return matches[0]


def plane_reference(value, model):
    reference = typed(value, "moCompRefPlane_c")
    component = typed(reference["f58"], "moUnitComponent_c")
    require(component["owner"] is model and reference["ff8"] is None,
            "offset source plane reference is not a registered datum in its owning part")
    return {"class": reference.cls, "map_slot": reference.index,
            "datum_id": reference["ff0"]["f00"], "datum_creation": reference["ff0"]["f08"],
            "principal_kind": reference["f100"], "component_map_slot": component.index}


def distance_geometry(node, model):
    geometry = typed(node, "moRefPlaneDistanceGeom_c")
    require(geometry["f40"] in (0, 1) and isfinite(geometry["f38"]),
            "distance geometry has a noncanonical reverse flag or nonfinite distance")
    wrapper = geometry["f08"]
    require(isinstance(wrapper, Obj) and isa(wrapper.cls, "moRefWrapper_c"),
            "distance geometry lost its selected wrapper")
    return {"class": geometry.cls, "map_slot": geometry.index,
            "distance_m": geometry["f38"], "reverse": bool(geometry["f40"]), "count": geometry["f44"],
            "selected_uv": [geometry["u"], geometry["v"]], "selected_point": vector(geometry["f20"]),
            "wrapper_class": wrapper.cls, "wrapper_map_slot": wrapper.index,
            "reference": plane_reference(wrapper["f58"], model)}


def parameter_rows(archive_map):
    result = []
    for slot, entry in archive_map.table.items():
        if entry[0] != "obj" or not isinstance(entry[1], Obj):
            continue
        node = entry[1]
        if node.cls not in ("moLengthParameter_c", "moAngleParameter_c", "moScalerParameter_c", "moIntegerParameter_c"):
            continue
        require(isfinite(node["f58"]), "source contains a nonfinite native parameter")
        result.append({"class": node.cls, "map_slot": slot, "value": node["f58"],
                       "name": node["f18"]["f08"] if isinstance(node.get("f18"), Obj) else None,
                       "alternate_name": node["f48"]["f08"] if isinstance(node.get("f48"), Obj) else None})
    return result


def project_offset(model, roots, archive_map, case, expected, snapshot):
    from ReferencePlaneSourcePlan import BASE_NAMES, BOSS, PLANE, SKETCH

    typed(model, "moPart_c")
    plane = named(roots, PLANE, "moRefPlane_c")
    support = named(roots, BASE_NAMES[case["base"]], "moRefPlane_c")
    profile = named(roots, SKETCH, "moProfileFeature_c")
    boss = named(roots, BOSS, "moExtrusion_c")
    data = plane["f6f8"]
    require(isinstance(data, Obj), "authored source plane has no typed plane-data owner")
    common = {"class": data.cls, "map_slot": data.index,
              "root_m": vector(data["root"]), "normal": vector(data["normal"]),
              "stored_transform": transform(data["f20"]),
              "border": [data[f"b{index}"] for index in range(4)],
              "modes": {key: data[key] for key in ("f50", "f54", "f58", "f5c", "f60", "f64")}}
    require(data.cls == "moConstraintRefplaneData_c",
            f"offset source selects {data.cls}, not the currently mapped constrained-distance branch")
    interface = typed(data["f88"], "moConstraintRefplaneInterfaceData_c")
    slots = [interface[key] for key in ("f08", "f10", "f18")]
    slot_rows = [None if node is None else distance_geometry(node, model) for node in slots]
    require(slot_rows[0] is not None and slot_rows[1:] == [None, None],
            "single first-reference offset source has a different ordered geometry triplet")
    distance = slot_rows[0]
    sketch_reference = plane_reference(profile["pd_f78"], model)
    depth_display = boss["f818"]["f18"]
    require(isinstance(depth_display, Obj) and isa(depth_display.cls, "moDisplayDim_c"),
            "source boss has no typed depth display")
    depth_handle, = [row["o"] for row in depth_display["f850"]]
    depth_parameter = depth_handle["ff0"]["f28"]
    checks = {
        "distance_matches_input": near([distance["distance_m"]], [expected["distance_m"]]),
        "distance_matches_native_api": near([distance["distance_m"]], [snapshot["plane"]["distance_m"]]),
        "reverse_matches_input": distance["reverse"] is case["reverse"],
        "single_plane_count": distance["count"] == 1,
        "selected_principal_id": distance["reference"]["datum_id"] == support["f08"],
        "selected_principal_kind": distance["reference"]["principal_kind"] == case_axis(case),
        "common_origin_matches_input": near(common["root_m"], expected["plane_origin"]),
        "common_normal_matches_input": near(common["normal"], expected["normal"]),
        "sketch_resolves_authored_plane": sketch_reference["datum_id"] == plane["f08"] and sketch_reference["principal_kind"] == 0,
        "boss_depth_matches_input": near([depth_parameter["f58"]], [expected["depth_m"]]),
    }
    return {"plane_feature_id": plane["f08"], "plane_map_slot": plane.index,
            "support_feature_id": support["f08"], "profile_feature_id": profile["f08"],
            "boss_feature_id": boss["f08"], "common_plane": common,
            "interface_map_slot": interface.index, "ordered_geometry_slots": slot_rows,
            "sketch_reference": sketch_reference, "sketch_stored_transform": transform(profile["pd_ff0"]),
            "boss_depth_m": depth_parameter["f58"], "native_parameters": parameter_rows(archive_map),
            "native_api_plane_transform": snapshot["plane"]["transform"],
            "checks": checks, "slot_correlations_passed": all(checks.values()),
            "runtime_owner_f10_not_serialized": True,
            "construction_concrete_class": "moConstraintDefaultPlaneRefplaneData_c",
            "published_archive_class": "moConstraintRefplaneData_c",
            "frame_direction_convention_qualified": False}


def case_axis(case):
    return {"right": 1, "top": 2, "front": 3}[case["base"]]
