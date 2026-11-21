from __future__ import annotations

import math

from SdkCircleHeldoutRules import analytic, require


def close(actual, expected, label, absolute=1e-12):
    require(type(actual) in (int, float) and type(expected) in (int, float) and
            math.isfinite(actual) and math.isfinite(expected) and
            math.isclose(actual, expected, rel_tol=2e-7, abs_tol=absolute), label + " differs")


def tree_rows(rows):
    result = []
    for row in rows:
        require(row.get("error") == 0 and row.get("warning") is False and row.get("suppressed") is False,
                "complete native tree contains an unhealthy or suppressed row")
        result.append([row["name"], row["type"], row["parent"]])
    return result


def check_extra(state, spec, expected_rows, factors):
    require(tree_rows(state["complete_tree"]) == expected_rows, "complete ordered native tree differs from authored system")
    require(state["configuration_names"] == [spec["configuration_name"]] and
            state["active_configuration"] == spec["configuration_name"], "named configuration ownership differs")
    require(state["visible_solid_count"] == state["solid_count"] == 1 and state["body_is_solid"] is True,
            "native model does not expose one actual visible solid")
    model = analytic(spec, *factors)
    mass = state["mass_properties"]
    require(type(mass) is dict and "error" not in mass and mass["mass"] > 0, "native mass measurement failed")
    close(mass["volume"], model["volume_m3"], "volume", 1e-22)
    close(mass["area"], model["area_m2"], "area", 1e-18)
    for index, value in enumerate(model["com_m"]):
        close(mass["com"][index], value, "centroid", 1e-10)
    for actual, expected in zip(state["extreme_bounds_m"], model["bounds_m"], strict=True):
        for value, wanted in zip(actual, expected, strict=True):
            close(value, wanted, "body extreme", 1e-10)
    counts = state["body_topology"]
    require(counts == {"faces": 3, "edges": 2, "vertices": 0} and
            all(type(value) is int for value in counts.values()),
            "closed circular prism topology must have three faces two circular edges and no end vertices")


def compare_extra(actual, expected):
    for name in ("complete_tree", "configuration_names", "active_configuration", "solid_count", "visible_solid_count", "body_is_solid", "body_topology"):
        require(actual[name] == expected[name], "paired complete native state differs: " + name)
    for name in ("volume", "area", "mass"):
        close(actual["mass_properties"][name], expected["mass_properties"][name], "paired " + name, 1e-22)
    close(actual["document_density_kg_m3"], expected["document_density_kg_m3"], "paired document density")
    for value, wanted in zip(actual["mass_properties"]["com"], expected["mass_properties"]["com"], strict=True):
        close(value, wanted, "paired centroid", 1e-10)
    for left, right in zip(actual["extreme_bounds_m"], expected["extreme_bounds_m"], strict=True):
        for value, wanted in zip(left, right, strict=True):
            close(value, wanted, "paired bound", 1e-10)


def compare_phases(actual, expected):
    require(actual["passed"] and expected["passed"] and actual["phase"] == expected["phase"], "paired lifecycle phase is incomplete")
    compare_extra(actual["initial_state"]["extra"], expected["initial_state"]["extra"])
    for key in ("snapshot", "edited_snapshot", "edited_body_snapshot", "edited_reverse_body_snapshot"):
        require((key in actual) == (key in expected), "paired driving edit evidence differs")
        if key in actual:
            compare_extra(actual[key]["extra"], expected[key]["extra"])
            for name in ("bodies", "whats_wrong", "constraint_status", "frame"):
                require(actual[key][name] == expected[key][name], "paired sketch ownership/frame differs: " + name)
            for value, wanted in zip(actual[key]["model_to_sketch_transform"], expected[key]["model_to_sketch_transform"], strict=True):
                close(value, wanted, "paired support transform", 1e-12)
    return {"passed": True, "full_tree": True, "configurations": True, "independent_geometry": True,
            "paired_mass_density": True, "actual_topology": True, "driving_edits": True}
