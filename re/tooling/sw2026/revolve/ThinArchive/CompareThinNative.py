from math import isclose

from RevolveFamilyModel import need


def confirm_number(actual, expected, *, mass=False):
    if mass:
        return ((abs(actual) <= 1e-12 and abs(expected) <= 1e-12)
                or format(actual, ".6g") == format(expected, ".6g"))
    return isclose(actual, expected, rel_tol=1e-13, abs_tol=1e-12)


def compare_points(actual, expected, label, *, mass=False):
    need(all(confirm_number(a, b, mass=mass) for a, b in zip(actual, expected, strict=True)), label)


def compare_definition(actual, expected):
    for name in ("is_thin", "is_boss", "type", "reverse", "axis_type", "wall_mode"):
        need(actual[name] == expected[name], "paired definition differs in " + name)
    for label in ("angles_rad", "wall_getters_m"):
        compare_points(actual[label], expected[label], "paired native " + label + " differs")
    for actual_point, wanted in zip(actual["axis"]["points"], expected["axis"]["points"], strict=True):
        compare_points(actual_point, wanted, "paired selected construction line differs")


def compare_profile(actual, expected):
    need(actual["configuration"] == expected["configuration"], "paired current configuration differs")
    for a, b in zip(actual["frame_points"], expected["frame_points"], strict=True):
        compare_points(a, b, "paired sketch frame differs")
    for a, b in zip(actual["segments"], expected["segments"], strict=True):
        need(a["kind"] == b["kind"] == "line" and a["construction"] == b["construction"],
             "paired sketch line or construction state differs")
        for label in ("start", "end"):
            compare_points(a[label], b[label], "paired ordered sketch endpoints differ")


def compare_drivers(actual, expected):
    need(tuple(actual) == tuple(expected), "paired editable driver inventory differs")
    for role, native in actual.items():
        target = expected[role]
        need(native["name"].split("@")[:2] == target["name"].split("@")[:2]
             and native["editable"] and target["editable"] and native["kind"] == target["kind"]
             and native["display_scale"] == target["display_scale"]
             and confirm_number(native["value"], target["value"]), "paired editable driver differs in " + role)


def compare_state(actual, expected):
    need(actual["body_count"] == expected["body_count"] == 1, "paired native solid count differs")
    need(actual["features"] == expected["features"], "paired full recursive native feature tree differs")
    need(actual["parents"] == expected["parents"] and actual["feature_type"] == expected["feature_type"],
         "paired dependency or thin feature type differs")
    need(actual["first_wall_sign"] == expected["first_wall_sign"], "paired signed wall side differs")
    compare_definition(actual["definition"], expected["definition"])
    compare_profile(actual["profile"], expected["profile"])
    compare_drivers(actual["drivers"], expected["drivers"])
    measured, source = (item["measured"] for item in (actual, expected))
    for label in ("name", "faces", "edges", "vertices"):
        need(measured[label] == source[label], "paired native body differs in " + label)
    for label in ("volume_m3", "area_m2"):
        need(confirm_number(measured[label], source[label], mass=True), "paired six-significant native " + label + " differs")
    for label in ("com_m", "bounds_m"):
        compare_points(measured[label], source[label], "paired six-significant " + label + " differs", mass=True)
    return {"tree_rows": len(actual["features"]), "body_name": measured["name"],
            "driver_count": len(actual["drivers"]), "numeric_geometry_checks": 11}


def compare_edits(actual, expected):
    need(actual["edit"]["passed"] and expected["edit"]["passed"], "paired native driver edit did not complete")
    for a, b in zip(actual["edit"]["dimensions"], expected["edit"]["dimensions"], strict=True):
        need(a["role"] == b["role"] and a["status"] == b["status"] == 0
             and a["dimension"].split("@")[:2] == b["dimension"].split("@")[:2]
             and confirm_number(a["before"], b["before"]) and confirm_number(a["after"], b["after"]),
             "paired native dimension identity or edit differs")


def compare_cycle(actual, expected, mode):
    need(len(actual) == len(expected) == 2, "paired saved lifecycle is incomplete")
    compare_edits(actual[0], expected[0])
    labels = ("reopened", "after-angle") + (("after-wall1",) if mode == "two" else ()) + ("edited",)
    results = {label: compare_state(actual[0][label], expected[0][label]) for label in labels}
    results["edited_fresh_reopen"] = compare_state(actual[1]["reopened"], expected[1]["reopened"])
    return results
