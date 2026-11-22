from hashlib import sha256
from json import loads
from math import dist, isclose

from ChamferModel import compare_six


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read_pinned(path, pin):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == pin, "protected source receipt differs")
    return loads(raw)


def points_match(actual, source):
    pending = list(source)
    require(len(actual) == len(pending), "native distance chamfer point counts differ")
    for point in actual:
        matches = [index for index, other in enumerate(pending) if dist(point, other) <= 1e-10]
        require(len(matches) == 1, "native distance chamfer points lack a unique physical match")
        pending.pop(matches[0])


def compare_state(actual, source):
    for key in ("tree", "configurations", "branch"):
        require(actual[key] == source[key], "source and candidate differ in the ordered native " + key)
    left, right = actual["definition"], source["definition"]
    require(left["type"] == right["type"] == "Chamfer" and left["parents"] == right["parents"],
            "source and candidate chamfer have different actual parents or operation")
    typed, wanted = left["fields"], right["fields"]
    require(typed.keys() == wanted.keys() and all(typed[key] == wanted[key]
            for key in typed if key != "distance_by_side_m"),
            "source and candidate differ in mode or native selected definitions")
    require(actual["drivers"].keys() == source["drivers"].keys(),
            "source and candidate have different independent editing roles")
    drivers = []
    for key, actual_driver in actual["drivers"].items():
        source_driver = source["drivers"][key]
        require(actual_driver["name"].split("@")[:2] == source_driver["name"].split("@")[:2]
                and all(actual_driver[field] == source_driver[field]
                    for field in ("display_kind", "index", "driven_state", "read_only"))
                and not actual_driver["read_only"], "source and candidate driver identity or editability differs")
        drivers.append((actual_driver["value_si"], source_driver["value_si"], 1e-12))
    stock, original_stock = actual["stock"], source["stock"]
    require(stock.keys() == original_stock.keys()
            and all(stock[key] == original_stock[key] for key in stock if key != "depth_m"),
            "source and candidate differ in the real predecessor history")
    require(all(isclose(a, b, abs_tol=1e-12, rel_tol=0.0) for a, b in
                zip(actual["profile"]["model_to_sketch"], source["profile"]["model_to_sketch"], strict=True)),
            "source and candidate sketch frames differ")
    body, original = actual["body"], source["body"]
    require(body["bodies"] == original["bodies"] == 1 and body["counts"] == original["counts"],
            "source and candidate solid incidence differs")
    for a, b in ((body["vertices_m"], original["vertices_m"]),
                 (actual["bevel"]["vertices_m"], source["bevel"]["vertices_m"]),
                 (left["edge"]["endpoints_m"], right["edge"]["endpoints_m"])):
        points_match(a, b)
    native, expected = body["native"], original["native"]
    values = [*drivers, (stock["depth_m"], original_stock["depth_m"], 1e-12),
              (native["volume"], expected["volume"], 1e-21),
              (native["area"], expected["area"], 1e-16),
              (actual["bevel"]["area_m2"], source["bevel"]["area_m2"], 1e-16)]
    for a, b, threshold in ((native["com"], expected["com"], 1e-10),
                             (body["bounds_m"], original["bounds_m"], 1e-10),
                             (typed["distance_by_side_m"], wanted["distance_by_side_m"], 1e-12),
                             (actual["face_areas_m2"], source["face_areas_m2"], 1e-16)):
        values.extend((x, y, threshold) for x, y in zip(a, b, strict=True))
    require(all(compare_six(x, y, tolerance)[2] for x, y, tolerance in values),
            "source and candidate numerical geometry differs at six significant figures")
    return len(values)


def compare_source(capture, case, states, pin):
    report = read_pinned(capture / "Result.json", pin)
    require(report["cohort"] == "heldout" and report["passed"]
            and report["idle_after"] and report["inputs_unchanged"]
            and report["control_before"]["passed"] and report["control_after"]["passed"],
            "protected source has incomplete independent native custody")
    (row,) = [item for item in report["cases"] if item["case"] == case["name"]]
    require(row["passed"] and row["snapshots"] == 4 and len(states) == 3,
            "protected source lacks its complete edit lifecycle")
    comparisons = 0
    for state, phase, key in zip(states, row["phases"], ("authored", "edited", "reopened"), strict=True):
        record = read_pinned(capture / case["name"] / phase["phase"] / "Record.json", phase["record_sha256"])
        require(record["passed"], "protected source phase did not pass")
        comparisons += compare_state(state, record[key])
    return comparisons
