from math import dist, isfinite
from struct import pack

from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, ReadRows, RequireNode

from PatternAngleGeometry import canonical_angle_geometry
from PatternAngleWire import ANGLE, ANGLE_PLANE, COINCIDENT, INTERFACE
from PatternHingeGeometry import AXIS, ORIGIN


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def point(fields):
    values = tuple(fields[axis] for axis in "xyz")
    require(all(type(value) is float and isfinite(value) for value in values), "invalid typed point or vector")
    return values


def node_fields(value, kind):
    return RequireNode(value, kind).FieldsValue


def matrix(transform):
    require(transform["has_matrix"] == 1 and transform["f70"] == 1.0 and transform["f78"] == 0,
            "the selected datum or angular driver has a nonrigid frame")
    return tuple(tuple(transform["f08"][f"m{3 * row + col}"] for row in range(3)) for col in range(3))


def roots_of_kind(roots, kind):
    return [node for node in roots if node is not None and node.ClassValue.NameValue == kind]


def selected_target(wrapper, component_kind, target_kind, model, roots, headers):
    require(wrapper["f60"] is None and wrapper["f68"] == 1 and (wrapper["has_f10"], wrapper["has_f18"]) == (0, 0),
            "expected a local, untransformed, resolved angle support")
    selection = node_fields(wrapper["f58"], component_kind)
    reference = RequireNode(selection["f58"], "moUnitComponent_c")
    require(reference.FieldsValue["owner"] is model and reference is not model.FieldsValue["f990"]
            and reference.FieldsValue["has_ext"] == 0 and selection["ff8"] is None,
            "angle support requires an exclusive local reference to a registered feature")
    key = selection["ff0"]["f00"]
    matches = [node for node in roots_of_kind(roots, target_kind) if node.FieldsValue["f08"] == key]
    require(len(matches) == 1 and all(selection["ff0"]["f08"] == DatumTime(header, key) for header in headers),
            "angle support does not join the actual registered target and both creation logs")
    return matches[0], reference


def annotation_catalog(model):
    values = model.FieldsValue
    collection = node_fields(values["fa48"], "suObList")
    rows = ReadRows(collection["items"])
    views = [node_fields(row["o"], "moAnnotationView_c") for row in rows]
    ids = [view["f360"] for view in views]
    names = [view["f358"] for view in views]
    require(collection["n"] == len(views) and len(ids) == len(set(ids)) == len(set(names))
            and all(type(key) is int and key > 199 for key in ids), "ambiguous or unregistered annotation view catalog")
    return views


def driver(model, feature, data, authored):
    display = node_fields(data["f150"], "moDisplayAngularDim_c")
    handles = ReadRows(display["f850"])
    require(display["n850"] == len(handles) == 1 and display["f6a0"]["f10"] == 13,
            "constrained datum requires one actual angular display and handle")
    handle = node_fields(handles[0]["o"], "moFeatureDimHandle_c")
    require(all(handle[key] is None for key in ("f58", "fe8", "f100", "f130", "f138", "f140", "f148")),
            "the angle display does not own a direct local dimension")
    dim = node_fields(handle["ff0"], "AngleDim_c")
    parameter = RequireNode(dim["f28"], "moAngleParameter_c")
    packed = display["f5b0"]
    require(ReadNodeName(parameter) == "D1" and dim["refcount"] == 1 and dim["ff8"] == 1
            and type(dim["f50"]) is int and 0 <= dim["f50"] < feature.FieldsValue["f08"]
            and parameter.FieldsValue["f58"] == authored and parameter.FieldsValue["f48"] is None
            and (packed["elem"], packed["alloc_a"], packed["alloc_b"], packed["n"], packed["data"])
            == (8, 16, 1, 1, pack("<d", authored)), "angular display value, driver or registered identity differs")
    slots = ReadRows(display["f2b0"])
    views = annotation_catalog(model)
    require(display["n2b0"] == len(slots) == 1, "expected a single explicit annotation view for the angular display")
    selected = [view for view in views if view["f360"] == slots[0]["v"]]
    require(len(selected) == 1 and selected[0]["f358"] == "*Back",
            "angle display view ID does not bind the actual *Back annotation view")
    view = selected[0]
    standards = [node_fields(row["o"], "moView_c") for row in ReadRows(model.FieldsValue["f9f8"])]
    standard_back = [standard for standard in standards if standard["f358"] == view["f358"]]
    require(len(standard_back) == 1 and standard_back[0]["f360"] != view["f360"] and dim["has_ff0"] == 1
            and matrix(view["f368"]) == matrix(dim["ff0"]), "angle owns an annotation-frame identity independent of a camera view")
    return display, dim, {"name": "D1", "id": dim["f50"], "angle_rad": authored,
                          "annotation_view": view["f358"], "annotation_view_id": view["f360"],
                          "standard_view_id": standard_back[0]["f360"]}


def prove_geometry(data, feature, display, dim, authored_geometry):
    vector_checks = [
        ("root", point(data["root"]), authored_geometry["root_m"], 0.0),
        ("normal", point(data["normal"]), authored_geometry["basis_u_v_n"][2], 2e-15),
        ("border", tuple(data[f"b{i}"] for i in range(4)), authored_geometry["ordered_borders_m"], 0.0),
        ("name_corner", point(feature.FieldsValue["f6c0"]), authored_geometry["name_corner_m"], 1e-16),
        ("dimension_shift", tuple(dim["ff0"][key] for key in ("f58", "f60", "f68")),
         authored_geometry["dimension_inverse_shift_m"], 1e-16),
        ("label_direction", point(display["f880"]), authored_geometry["label_direction"], 2e-15),
        ("label_radius", (display["f8b0"],), (authored_geometry["label_radius_m"],), 1e-16),
        ("ray_separation", (display["fad0"],), (authored_geometry["ray_separation_m"],), 1e-16),
    ]
    vector_checks.extend(("basis_" + axis, actual, predicted, 2e-15) for axis, actual, predicted in
                         zip("uvn", matrix(data["f20"]), authored_geometry["basis_u_v_n"], strict=True))
    vector_checks.extend(("witness_" + key, point(dim[key]), predicted, 1e-16) for key, predicted in
                         zip(("f80", "fa0", "fc0"), authored_geometry["witness_points_m"], strict=True))
    require(matrix(dim["ff0"]) == authored_geometry["dimension_basis"] and display["f100c"] == 1,
            "angle presentation's local base axes or live arc mode differs")
    errors = {name: dist(actual, predicted) for name, actual, predicted, _ in vector_checks}
    require(all(errors[name] <= limit for name, _, _, limit in vector_checks),
            "stored angle presentation differs from independently authored hinge and angle")
    return errors


def check_angles(model, roots, headers, ends, authored_angle):
    features = [root for root in roots_of_kind(roots, "moRefPlane_c")
                if root.FieldsValue["f6f8"] is not None and root.FieldsValue["f6f8"].ClassValue.NameValue == ANGLE_PLANE]
    require(len(features) == 1, "expected one actual constrained angular datum feature")
    feature = features[0]
    data = node_fields(feature.FieldsValue["f6f8"], ANGLE_PLANE)
    interface = node_fields(data["f88"], INTERFACE)
    angle = node_fields(interface["f08"], ANGLE)
    coincident = node_fields(interface["f10"], COINCIDENT)
    third = node_fields(interface["f18"], COINCIDENT)
    require(third["f08"] is None and interface["f18"] is not interface["f10"] and angle["f40"] == 0
            and all((row["u"], row["v"], point(row["f20"])) == (0.5, 0.5, ORIGIN) for row in (angle, coincident, third)),
            "angle datum requires its default pick locations and a present unselected third geometry")
    require(angle["f38"] == authored_angle and (data["f5c"], data["f54"], data["f58"], data["f148"]) == (22, -4, -4, -3),
            "constrained angle or canonical signed frame selector differs")
    right, plane_owner = selected_target(node_fields(angle["f08"], "moPlaneRef_w"), "moCompRefPlane_c", "moRefPlane_c", model, roots, headers)
    line = node_fields(coincident["f08"], "moLineRef_w")
    axis, axis_owner = selected_target(line, "moCompRefAxis_c", "moRefAxis_c", model, roots, headers)
    axis_data = node_fields(axis.FieldsValue["f700"], "moPlaneInterAxisData_c")
    supports = tuple(selected_target(node_fields(axis_data[key], "moPlaneRef_w"), "moCompRefPlane_c", "moRefPlane_c", model, roots, headers)
                     for key in ("f80", "f88"))
    require(supports[1][0] is right and [ReadNodeName(item[0]) for item in supports] == ["Top Plane", "Right Plane"]
            and len({plane_owner, axis_owner, *(item[1] for item in supports)}) == 4,
            "selected Right plane and hinge supports have crossed roles or component identities")
    start, finish = ends
    require((point(axis_data["f18"]), point(axis_data["f30"])) == ends
            and point(line["fc8"]) == start and point(line["fe0"]) == AXIS
            and (line["fb0"], line["fb8"], line["ff8"]) == (0.0, start[2] - finish[2], 0),
            "selected coincident line does not represent the actual finite hinge")
    display, dim, driver_result = driver(model, feature, data, authored_angle)
    geometry = canonical_angle_geometry(*ends, authored_angle)
    return {"feature": {"name": ReadNodeName(feature), "id": feature.FieldsValue["f08"],
                        "constraint_slots": [ANGLE, COINCIDENT, COINCIDENT],
                        "mode": data["f5c"], "signed_selector": data["f148"], "selected_endpoints_m": ends},
            "selected_ids": {"right": right.FieldsValue["f08"], "hinge": axis.FieldsValue["f08"]},
            "driver": driver_result, "geometry_prediction": geometry,
            "geometry_errors": prove_geometry(data, feature, display, dim, geometry)}
