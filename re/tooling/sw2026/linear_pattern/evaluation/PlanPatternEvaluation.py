from math import dist, isclose, isfinite, sqrt
from pathlib import PureWindowsPath
import re


SLOTS = ("Slot01", "Slot02")
STATES = ("original", "spacing", "instances")
DRIVERS = {"spacing": "D3", "instances": "D1"}
LABELS = ("PlateSketch", "PlateBoss", "SeedSketch", "SeedBoss", "EnvelopeHinge", "EnvelopeDirection", "LinearPattern")
BACK = ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0))
TOP = ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def close(left, right, tolerance=1e-12):
    return isclose(left, right, rel_tol=5e-7, abs_tol=tolerance)


def planned(source, candidate, epoch, angle):
    input_leaf = PureWindowsPath(source["filenames"]["original"])
    require(source["slot"] in SLOTS and re.fullmatch(r"Pattern-[0-9a-f]{32}\.SLDPRT", input_leaf.name)
            and input_leaf.name == source["filenames"]["original"] and candidate.name == input_leaf.name
            and candidate.is_absolute() and candidate.drive == "C:" and type(epoch) is int and epoch > 0,
            "unexpected opaque held-out slot or modeled Windows locator")
    require(set(source["filenames"]) == set(STATES)
            and source["filenames"]["spacing"] == input_leaf.stem + "-Pitch.SLDPRT"
            and source["filenames"]["instances"] == input_leaf.stem + "-Count.SLDPRT",
            "invalid local source derivative identities")
    frozen = source["design"]
    require(set(frozen["states"]) == set(STATES), "source lock has alternate authored states")
    plate, seed = frozen["plate_box_m"], frozen["seed_box_m"]
    plate_sketch, plate_feature, seed_sketch, seed_feature, hinge, datum, pattern = LABELS
    seed_centre = [(low + high) / 2.0 for low, high in zip(*seed, strict=True)]
    seed_centre[2] = 0.0
    origins = {"D1": seed_centre, "D2": seed[0]}
    styles = [{"name": label, "annotation_view": "*Back" if label == "D1" else None,
               "label_m": origins.get(label, [0.0, 0.0, 0.0]), "design_intent": True, "selected_leader": 0}
              for label in ("D1", "D3", "D2", "D4", "D5", "D6")]
    component = 1.0 / sqrt(2.0)
    direction = [component, -component, 0.0]
    model = {
        "seed": {"name": input_leaf.stem, "configuration": "Default", "path": str(candidate),
                 "epoch": epoch, "plate": {"sketch": plate_sketch, "feature": plate_feature, "bounds_m": plate},
                 "seed": {"sketch": seed_sketch, "feature": seed_feature, "bounds_m": seed}},
        "axis": hinge,
        "plane": {"name": datum, "angle_rad": angle, "reverse": False, "annotation_view": "*Back",
                  "design_intent": True, "selected_leader": 0, "shifted_point_m": [0.0, 0.0, 0.0]},
        "annotation": {"views": [{"name": "*Top", "basis": TOP}, {"name": "*Back", "basis": BACK}],
                       "active": None, "shown": [None]},
    }
    cases = {}
    for role in STATES:
        target = frozen["states"][role]
        count, pitch = target["count"], target["spacing_m"]
        require(type(count) is int and 2 <= count <= 8 and type(pitch) is float and 0.0 < pitch < 1.0,
                "locked driver values escaped the disclosed example profile")
        expected = target["expected_final"]
        corners = [list(point) for point in (
            *[(x, y, z) for x in (plate[0][0], plate[1][0]) for y in (plate[0][1], plate[1][1]) for z in (plate[0][2], plate[1][2])],
            *[(x + direction[0] * column * pitch, y + direction[1] * column * pitch, z)
              for column in range(count) for x in (seed[0][0], seed[1][0]) for y in (seed[0][1], seed[1][1])
              for z in (plate[1][2], seed[1][2])],
        )]
        cases[role] = {
            "modeled_input": {**model, "pattern": {"name": pattern, "count": count, "pitch_m": pitch,
                                                   "reverse": False, "styles": styles}},
            "independent_cell_measure": {"signed_direction": direction, "body_count": 1, "face_count": 6 + 5 * count,
                                         "vertices_m": corners,
                                         **{key: expected[key] for key in ("volume_m3", "area_m2", "centroid_m", "bounds_m")}},
        }
    a, b, c = (cases[role]["modeled_input"]["pattern"] for role in STATES)
    require(a["pitch_m"] < b["pitch_m"] and a["count"] == b["count"]
            and a["pitch_m"] == c["pitch_m"] and a["count"] + 1 == c["count"],
            "held-out branches must independently change pitch and count")
    return cases


def match_points(actual, expected, tolerance=1e-9):
    remaining = list(expected)
    require(len(actual) == len(remaining), "different physical vertex or sketch point count")
    for point in actual:
        matches = [index for index, target in enumerate(remaining) if dist(point, target) <= tolerance]
        require(len(matches) == 1, "missing or ambiguous physical vertex or sketch point")
        remaining.pop(matches[0])


def compare_geometry(actual, expected):
    require(actual["body_count"] == expected["body_count"] and actual["face_count"] == expected["face_count"]
            and not actual["rebuild_diagnostics"] and not actual["feature_diagnostics"], "native solids or topology differ")
    a, b = actual["mass"], expected["mass"]
    require(all(isfinite(row["mass"]) and row["mass"] > 0.0 for row in (a, b))
            and all(close(a[key], b[key], 1e-18) for key in ("area", "volume", "mass"))
            and dist(a["com"], b["com"]) <= 1e-10
            and all(close(x, y, 1e-9) for x, y in zip(actual["bounds_m"], expected["bounds_m"], strict=True)),
            "native mass, area, volume, centre or bounds differ")
    match_points(actual["vertices_m"], expected["vertices_m"])


def compare_datum(actual, expected):
    require(actual["reverse"] is expected["reverse"]
            and actual["hinge"]["parents"] == expected["hinge"]["parents"], "native datum ownership differs")
    for field in ("origin_m", "normal", "signed_normal", "transform"):
        require(all(close(a, b) for a, b in zip(actual[field], expected[field], strict=True)),
                "native datum frame differs at " + field)
    require(dist(actual["hinge"]["unit"], expected["hinge"]["unit"]) <= 1e-10,
            "actual hinge direction changed")
    for a, b in zip(actual["constraints"], expected["constraints"], strict=True):
        require(a["flags"] == b["flags"] and close(a["angle_or_distance"], b["angle_or_distance"]),
                "native datum constraint form or angle changed")


def compare_native(actual, expected):
    require(actual["tree"] == expected["tree"], "full ordered native feature tree differs")
    for key in ("dependencies", "boss_modes", "pattern_mode", "driver_owners"):
        require(actual[key] == expected[key], "native scope, tree owner, or driving dimension differs at " + key)
    require(actual["pattern"]["parents"] == expected["pattern"]["parents"]
            and all(close(actual["pattern"]["drivers"][key], expected["pattern"]["drivers"][key]) for key in ("D1", "D3")),
            "native patterned amounts or actual direct parents differ")
    compare_datum(actual["datum"], expected["datum"])
    for key, other in zip(actual["profiles"], expected["profiles"], strict=True):
        require(all(close(a, b) for a, b in zip(key["model_to_sketch"], other["model_to_sketch"], strict=True)),
                "native profile reference frame differs")
        actual_lines = list(key["geometry"])
        remaining = list(other["geometry"])
        require(len(actual_lines) == len(remaining) == 4, "native rectangle boundary inventory differs")
        for line in actual_lines:
            crossings = [idx for idx, target in enumerate(remaining)
                         if line["kind"] == target["kind"] == "line"
                         and all(line.get(field) == target.get(field) for field in ("construction",))
                         and ((dist(line["start"], target["start"]) < 1e-9 and dist(line["end"], target["end"]) < 1e-9)
                              or (dist(line["start"], target["end"]) < 1e-9 and dist(line["end"], target["start"]) < 1e-9))]
            require(len(crossings) == 1, "missing or ambiguous native profile edge")
            remaining.pop(crossings[0])
    compare_geometry(actual["geometry"], expected["geometry"])
