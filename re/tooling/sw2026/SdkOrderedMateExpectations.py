from __future__ import annotations

from copy import deepcopy
import math

from AuthorCurves import require
from PlanarMateEdit import check_satisfied, predict_edit, verify_case
from PrepareDimensionedAssemblyPredictions import occurrence
from PrepareSdkAssemblyNative import tree_rows


KINDS = {"coincident": (0, "MateCoincident"), "parallel": (3, "MateParallel"), "distance": (5, "MateDistanceDim")}


def close_values(actual, expected, absolute=1e-12):
    return len(actual) == len(expected) and all(
        math.isclose(left, right, rel_tol=1e-9, abs_tol=absolute)
        for left, right in zip(actual, expected, strict=True)
    )


def placement_transform(row):
    return occurrence(row)[1]


def authored_transform(row):
    u, v = row["u"], row["v"]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    return [*u, *v, *n, *row["origin"], 1.0, 0.0, 0.0, 0.0]


def generated_case(request, prediction):
    require(len(request["occurrences"]) == 2 and len(request["mates"]) == 3,
            "the ordered trial requires exactly two occurrences and three authored mates")
    placements = []
    for row in request["occurrences"]:
        u, v = row["u"], row["v"]
        require(close_values(u, [v[1], -v[0], 0.0]) and close_values(v, [-u[1], u[0], 0.0])
                and math.isclose(math.hypot(u[0], u[1]), 1.0, abs_tol=1e-14),
                "this observer admits proper rotations about Z only")
        placements.append({"axis": "z", "angle_deg": math.degrees(math.atan2(u[1], u[0])), "translation_m": row["origin"]})
        require(close_values(placement_transform(placements[-1]), authored_transform(row), 1e-14),
                "the pure native placement adapter changed an authored frame")
    planes = request["assembly"]["system"]["planes"]
    mates = []
    for row in request["mates"]:
        require(row["kind"] in KINDS and row["fixed_occurrence"] == 0,
                "the ordered native trial needs its supported kinds and fixed first occurrence")
        mate = {"kind": row["kind"], "name": row["name"], "planes": [[index, planes[row["axis"]]] for index in range(2)]}
        if row["kind"] == "distance":
            mate["distance_m"] = row["distance_m"]
        mates.append(mate)
    case = {"name": request["assembly"]["name"], "split": "discovery", "fixed_occurrence": 0, "placements": placements, "mates": mates}
    verify_case(case, 0, prediction["edit"]["new_value_m"])
    edit = predict_edit(case, prediction["edit"]["new_value_m"], placement_transform)
    return case, edit


def expected_trees(request):
    adapted = deepcopy(request)
    adapted["mate"] = adapted["mates"][0]
    trees = tree_rows(adapted)
    group = request["assembly"]["system"]["mate_group_name"]
    trees["parent"][-1:] = [[row["name"], KINDS[row["kind"]][1], group] for row in request["mates"]]
    return trees


def predicted_geometry(request):
    document = request["child"]["document"]
    require(document["units"]["value"] == "mm" and len(document["sketches"]["$tuple"]) == 1,
            "the fixture must retain its authored millimetre plain rectangle")
    sketch, = document["sketches"]["$tuple"]
    require(not sketch["parameter_ids"]["$tuple"] and len(sketch["entities"]["$tuple"]) == 4,
            "the SDK child must not acquire sketch driving dimensions")
    points = [[row["geometry"]["start"][axis] * 0.001 for axis in ("x", "y")] for row in sketch["entities"]["$tuple"]]
    width, height = [max(point[axis] for point in points) - min(point[axis] for point in points) for axis in range(2)]
    require(set(map(tuple, points)) == {(x * width / 2, y * height / 2) for x in (-1, 1) for y in (-1, 1)},
            "the independent child prediction requires the authored centered rectangle")
    boss, = document["feature_timeline"]["$tuple"]
    depth = boss["definition"]["length"]["value"] * 0.001
    require(depth > 0 and boss["definition"]["length"]["unit"] == "mm", "the child depth must be an authored positive millimetre length")
    return {"width": width, "height": height, "depth": depth}


def verify_predictions(request, prediction):
    require(prediction["heldout_inputs_read"] == 0 and prediction["source_observations_read"] == 0
            and prediction["geometry_prediction_uses_writer_frames_or_readback"] is False
            and prediction["save_order"] == ["child", "parent"], "the independent prediction provenance or save order differs")
    case, edit = generated_case(request, prediction)
    require(expected_trees(request) == prediction["tree"], "the full native trees differ from their authored role expansion")
    dimensions = predicted_geometry(request)
    require(dimensions == prediction["child_dimensions_m"], "the independent child dimensions differ from the neutral request")
    config, = request["child"]["document"]["configurations"]["$tuple"]
    require(prediction["assembly_configuration"] == request["assembly"]["configuration_name"] and
            prediction["child_configuration"] == config["name"] and config["active"], "the intended active configurations differ")
    require(prediction["child_parameters_m"] == {"D1@Boss-Extrude1": dimensions["depth"], "D1@Sketch1": None, "D2@Sketch1": None},
            "the independent child live dimension expectations differ")
    width, height, depth = (dimensions[key] for key in ("width", "height", "depth"))
    child = {"body_count": 1, "volume": width * height * depth, "area": 2 * (width * height + width * depth + height * depth), "com": [0.0, 0.0, depth / 2]}
    endpoint_names = [row["name"] for row in request["occurrences"]]
    endpoints = [{"mate": row["name"], "kind": row["kind"], "occurrences": endpoint_names,
                  "datums": [plane for _, plane in row["planes"]]} for row in case["mates"]]
    require(endpoints == prediction["ordered_endpoints"], "the ordered authored mate endpoints differ")
    for scope, expected_case in (("initial", case), ("edited", edit)):
        expected = prediction[scope]
        transforms = [placement_transform(row) for row in expected_case["placements"]]
        require(all(close_values(left, right, 1e-14) for left, right in zip(transforms, expected["occurrence_transforms"], strict=True)),
                "the native observer placement adapter differs from the independent before/edit prediction")
        check_satisfied(expected_case["mates"], transforms)
        require(expected["body_count"] == 2 and expected["fixed_flags"] == [True, False] and expected["child"] == child,
                "the authored body count, fixed anchor or child geometry differs")
        centers = [[matrix[9 + axis] + matrix[6 + axis] * depth / 2 for axis in range(3)] for matrix in transforms]
        mass = expected["assembly"]
        require(close_values([mass["volume"], mass["area"]], [2 * child["volume"], 2 * child["area"]], 1e-15)
                and close_values(mass["com"], [(left + right) / 2 for left, right in zip(*centers, strict=True)], 1e-14),
                "the independently computed assembly geometry differs")
        for mate, relation in zip(expected_case["mates"], expected["constraints"], strict=True):
            axis = {"Right Plane": 0, "Top Plane": 1, "Front Plane": 2}[mate["planes"][0][1]]
            normal = transforms[0][axis * 3:axis * 3 + 3]
            offset = math.fsum((transforms[1][9 + index] - transforms[0][9 + index]) * normal[index] for index in range(3))
            require((relation["name"], relation["kind"], relation["datum"], relation["distance_m"]) ==
                    (mate["name"], mate["kind"], mate["planes"][0][1], mate.get("distance_m"))
                    and math.isclose(relation["normal_dot"], 1.0, abs_tol=1e-14)
                    and math.isclose(relation["signed_offset_m"], offset, rel_tol=0.0, abs_tol=1e-14),
                    "the independent ordered constraint prediction differs")
    drive = next(row for row in case["mates"] if row["kind"] == "distance")
    parameter = "D1@" + drive["name"]
    require(prediction["edit"]["parameter"] == parameter and prediction["edit"]["full_name"] == parameter + "@" + case["name"] + ".Assembly",
            "the live distance edit target differs from its actual owning mate")
    return case, edit


def state_matches(value, expected, prediction):
    for key, role in (("tree", "parent"), ("child_tree", "child")):
        rows = value.get(key, ())
        if [[row["name"], row["type"], row["parent"]] for row in rows] != prediction["tree"][role] or any(row["suppressed"] for row in rows):
            return False
    rows = value["occurrences"]
    if (value["body_count"] != expected["body_count"] or [row["fixed"] for row in rows] != expected["fixed_flags"] or
            [row["configuration"] for row in rows] != [prediction["child_configuration"]] * 2 or
            any(not close_values(row["transform"], target) for row, target in zip(rows, expected["occurrence_transforms"], strict=True))):
        return False
    if len(value["mates"]) != len(prediction["ordered_endpoints"]):
        return False
    for mate, endpoint, constraint in zip(value["mates"], prediction["ordered_endpoints"], expected["constraints"], strict=True):
        if (mate["name"], mate["type"], mate["alignment"], [row["occurrence"] for row in mate["entities"]]) != (
                endpoint["mate"], KINDS[endpoint["kind"]][0], 0, endpoint["occurrences"]):
            return False
        if endpoint["kind"] == "distance" and (mate.get("flipped") is not False or mate["dimension_name"] != prediction["edit"]["full_name"]
                or not math.isclose(mate["dimension_m"], constraint["distance_m"], rel_tol=0.0, abs_tol=1e-12)):
            return False
        first, second = mate["entities"]
        dot = math.fsum(a * b for a, b in zip(first["normal"], second["normal"], strict=True))
        residual = math.fsum((b - a) * n for a, b, n in zip(first["point"], second["point"], first["normal"], strict=True))
        if not math.isclose(abs(dot), 1.0, abs_tol=1e-10) or not math.isclose(abs(residual), abs(constraint["signed_offset_m"]), rel_tol=1e-9, abs_tol=1e-10):
            return False
    for key, measured in (("assembly", value["mass"]), ("child", value["child_mass"])):
        target = expected[key]
        if not close_values([measured["volume"], measured["area"], *measured["com"]], [target["volume"], target["area"], *target["com"]], 1e-12):
            return False
    return True
