from math import dist, isclose

from ChamferModel import ROLES, compare_six, values_si
from FilletModel import require

DRIVER_NAMES = dict(zip(ROLES, ("D1", "D2"), strict=True))


def points_match(actual, expected):
    pending = list(expected)
    require(len(actual) == len(pending), "native point counts differ")
    for point in actual:
        matches = [index for index, other in enumerate(pending)
                   if len(point) == len(other) == 3 and dist(point, other) <= 1e-10]
        require(len(matches) == 1, "native geometry does not join one unambiguous physical point")
        pending.pop(matches[0])


def driver_roles(state, stem, case, edited):
    drivers = state["drivers"]
    require(set(drivers) == set(DRIVER_NAMES), "native source and generated files must expose both live handles")
    result = {}
    for role, want in zip(ROLES, values_si(case, edited), strict=True):
        row = drivers[role]
        qualified = row["name"].split("@")
        require(len(qualified) == 3 and qualified[:2] == [DRIVER_NAMES[role], "DistanceAngleEdgeChamfer"]
                and qualified[2].casefold() == (stem + ".Part").casefold()
                and row["driven_state"] == 2 and row["read_only"] is False
                and isclose(row["value_si"], want, rel_tol=0, abs_tol=1e-12),
                "the live chamfer driver differs in own name, owner, editability or value")
        result[role] = (row["display_kind"], row["index"], row["driven_state"], row["read_only"])
    return result


def compare_state(actual, expected, case, *, edited, actual_saved=True):
    stem = case["name"] + ("Edited" if edited and actual_saved else "")
    source_stem = case["name"] + ("Edited" if edited else "")
    require(actual["tree"] == expected["tree"] and actual["configurations"] == expected["configurations"] == ["Default"],
            "complete ordered native tree or ordinary configuration differs from the source")
    require(actual["branch"] == expected["branch"] and actual["definition"]["parents"] == expected["definition"]["parents"],
            "actual selected chamfer side or ordered parent ownership differs")
    require(actual["definition"]["type"] == expected["definition"]["type"] == "Chamfer",
            "the generated feature did not retain the actual native operation type")
    typed, wanted = actual["definition"]["fields"], expected["definition"]["fields"]
    numeric_options = {"distance_by_side_m", "EdgeChamferAngle"}
    require(typed.keys() == wanted.keys()
            and all(typed[key] == wanted[key] for key in typed.keys() - numeric_options),
            "native side selection, modes or alternate selection identities differ")
    require(driver_roles(actual, stem, case, edited) == driver_roles(expected, source_stem, case, edited),
            "the two editable native handles differ in index or display kind")
    stock, source_stock = actual["stock"], expected["stock"]
    require(stock.keys() == source_stock.keys()
            and all(stock[key] == source_stock[key] for key in stock.keys() - {"depth_m"}),
            "actual blind producer mode, sketch or child ownership differs")
    for left, right in zip(actual["profile"]["model_to_sketch"], expected["profile"]["model_to_sketch"], strict=True):
        require(isclose(left, right, rel_tol=0, abs_tol=1e-12), "actual sketch support transform differs")
    body, original = actual["body"], expected["body"]
    require(body["bodies"] == original["bodies"] == 1
            and body["counts"] == original["counts"] == {"faces": 7, "edges": 15, "vertices": 10},
            "actual physical counts differ")
    points_match(body["vertices_m"], original["vertices_m"])
    points_match(actual["bevel"]["vertices_m"], expected["bevel"]["vertices_m"])
    points_match(actual["definition"]["edge"]["endpoints_m"], expected["definition"]["edge"]["endpoints_m"])
    require(len(set(actual["definition"]["edge"]["adjacent_face_references"])) == 2
            and len(set(expected["definition"]["edge"]["adjacent_face_references"])) == 2,
            "native rollback did not resolve two distinct actual support faces")
    numeric = [(stock["depth_m"], source_stock["depth_m"], 1e-12),
               (typed["EdgeChamferAngle"], wanted["EdgeChamferAngle"], 1e-12),
               (body["native"]["volume"], original["native"]["volume"], 1e-21),
               (body["native"]["area"], original["native"]["area"], 1e-16),
               (actual["bevel"]["area_m2"], expected["bevel"]["area_m2"], 1e-16)]
    for left, right, floor in ((typed["distance_by_side_m"], wanted["distance_by_side_m"], 1e-12),
                               (body["native"]["com"], original["native"]["com"], 1e-10),
                               (body["bounds_m"], original["bounds_m"], 1e-10),
                               (actual["face_areas_m2"], expected["face_areas_m2"], 1e-16)):
        numeric.extend((a, b, floor) for a, b in zip(left, right, strict=True))
    for value, source_value, floor in numeric:
        require(compare_six(value, source_value, floor)[2], "actual source and generated numeric property differ at six significant figures")
    return len(numeric)
