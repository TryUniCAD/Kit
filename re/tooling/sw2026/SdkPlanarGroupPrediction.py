from copy import deepcopy
import math

from AuthorCurves import require
from PlanarMateEdit import PLANE_AXES, check_satisfied, predict_edit, verify_case
from PrepareSdkAssemblyNative import tree_rows


KINDS = {"coincident": (0, "MateCoincident"), "parallel": (3, "MateParallel"), "distance": (5, "MateDistanceDim")}


def transform(placement):
    axis = "xyz".index(placement["axis"])
    angle = math.radians(placement["angle_deg"])
    c, s = math.cos(angle), math.sin(angle)
    rows = {0: [1., 0., 0., 0., c, s, 0., -s, c], 1: [c, 0., -s, 0., 1., 0., s, 0., c], 2: [c, s, 0., -s, c, 0., 0., 0., 1.]}[axis]
    return [*rows, *placement["translation_m"], 1., 0., 0., 0.]


def expected_trees(request):
    adapted = deepcopy(request)
    adapted["mate"] = request["mates"][0]
    value = tree_rows(adapted)
    group = request["assembly"]["system"]["mate_group_name"]
    value["parent"][-1:] = [[row["name"], KINDS[row["kind"]][1], group] for row in request["mates"]]
    return {key: value[key] for key in ("parent", "child")}


def child_geometry(request):
    document = request["child"]["document"]
    require(document["units"]["value"] == "mm" and "rectangle_dimensions" in request["child"], "the controlled group requires its actual dimensioned millimetre rectangle")
    sketch, = document["sketches"]["$tuple"]
    feature, = document["feature_timeline"]["$tuple"]
    vertices = [[row["geometry"]["start"][axis] * .001 for axis in ("x", "y")] for row in sketch["entities"]["$tuple"]]
    width, height = [max(row[axis] for row in vertices) - min(row[axis] for row in vertices) for axis in range(2)]
    require(set(map(tuple, vertices)) == {(x * width / 2, y * height / 2) for x in (-1, 1) for y in (-1, 1)}, "this native group observer requires an independently authored centered rectangle")
    require(len(sketch["constraints"]["$tuple"]) == 6 and len(sketch["parameter_ids"]["$tuple"]) == 2, "the group child must retain all six actual sketch relations and both driving dimensions")
    depth = feature["definition"]["length"]["value"] * .001
    require(feature["definition"]["length"]["unit"] == "mm" and feature["definition"]["end_condition"]["value"] == "blind" and not feature["definition"]["reversed"] and not feature["definition"]["symmetric"], "the native group child requires the measured positive forward blind boss")
    return {"width": width, "height": height, "depth": depth}, {"volume": width * height * depth, "area": 2 * (width * height + width * depth + height * depth), "com": [0., 0., depth / 2], "body_count": 1}


def predict(request, case, edited_distance):
    require(len(case["placements"]) == len(request["occurrences"]) and case["fixed_occurrence"] == request["fixed_occurrence"], "the independently authored native case changes occurrence count or anchor")
    verify_case(case, request["fixed_occurrence"], edited_distance)
    for placement, row in zip(case["placements"], request["occurrences"], strict=True):
        matrix = transform(placement)
        raw = [*row["u"], *row["v"], 0., 0., 0., *row["origin"]]
        require(all(math.isclose(matrix[index], raw[index], rel_tol=1e-12, abs_tol=1e-14) for index in (*range(6), 9, 10, 11)), "the independent API transform differs from the authored neutral occurrence")
    require(len(case["mates"]) == len(request["mates"]), "the native case changed the complete mate count")
    for native, authored in zip(case["mates"], request["mates"], strict=True):
        expected = [[row["occurrence"], request["child"]["settings"]["system"]["planes"][row["axis"]]] for row in authored["endpoints"]]
        require((native["kind"], native["name"], native["planes"]) == (authored["kind"], authored["name"], expected), "native mate order or actual endpoint ownership differs from the neutral request")
    size, child = child_geometry(request)
    edit = predict_edit(case, edited_distance, transform)
    count = len(case["placements"])
    states = {}
    for name, selected in (("initial", case), ("edited", edit)):
        matrices = [transform(row) for row in selected["placements"]]
        check_satisfied(selected["mates"], matrices)
        centers = [[matrix[9 + axis] + matrix[6 + axis] * size["depth"] / 2 for axis in range(3)] for matrix in matrices]
        states[name] = {"body_count": count, "fixed_flags": [index == case["fixed_occurrence"] for index in range(count)], "occurrence_transforms": matrices,
                        "assembly": {"volume": count * child["volume"], "area": count * child["area"], "com": [math.fsum(row[axis] for row in centers) / count for axis in range(3)]}, "child": child,
                        "mate_values_m": [row.get("distance_m") for row in selected["mates"]]}
    config, = request["child"]["document"]["configurations"]["$tuple"]
    return {"schema": "kit.sw2026.sdk-planar-group-independent-prediction.v1", "case": case, "edited_case": edit, "edit_distance_m": edited_distance,
            "child_dimensions_m": size, "child_configuration": config["name"], "assembly_configuration": request["assembly"]["configuration_name"],
            "child_parameters_m": {"D1@Sketch1": size["width"], "D2@Sketch1": size["height"], "D1@Boss-Extrude1": size["depth"]},
            "occurrence_names": [row["name"] for row in request["occurrences"]], "tree": expected_trees(request), **states,
            "writer_frames_or_readback_used": False, "source_observations_read": 0, "heldout_inputs_read": 0, "native_acceptance": False}


def state_matches(value, expected, prediction):
    for field, key in (("tree", "parent"), ("child_tree", "child")):
        if [[row["name"], row["type"], row["parent"]] for row in value[field]] != prediction["tree"][key] or any(row["suppressed"] for row in value[field]):
            return False
    if value["body_count"] != expected["body_count"] or [row["name"] for row in value["occurrences"]] != prediction["occurrence_names"] or [row["fixed"] for row in value["occurrences"]] != expected["fixed_flags"]:
        return False
    for row, matrix in zip(value["occurrences"], expected["occurrence_transforms"], strict=True):
        if row["configuration"] != prediction["child_configuration"] or not all(math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12) for a, b in zip(row["transform"], matrix, strict=True)):
            return False
    if len(value["mates"]) != len(prediction["case"]["mates"]):
        return False
    for row, spec, length in zip(value["mates"], prediction["case"]["mates"], expected["mate_values_m"], strict=True):
        names = [prediction["occurrence_names"][index] for index, _ in spec["planes"]]
        if (row["name"], row["type"], row["alignment"], [end["occurrence"] for end in row["entities"]]) != (spec["name"], KINDS[spec["kind"]][0], 0, names):
            return False
        if length is not None and (row.get("flipped") is not False or row["dimension_name"] != "D1@" + spec["name"] + "@" + prediction["case"]["name"] + ".Assembly" or not math.isclose(row["dimension_m"], length, rel_tol=0., abs_tol=1e-12)):
            return False
    return all(all(math.isclose(a, b, rel_tol=5e-7, abs_tol=1e-12) for a, b in zip([actual["volume"], actual["area"], *actual["com"]], [target["volume"], target["area"], *target["com"]], strict=True)) for actual, target in ((value["mass"], expected["assembly"]), (value["child_mass"], expected["child"])))
