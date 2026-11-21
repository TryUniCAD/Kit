import math
import re

SCHEMA = "kit.sw2026.standard-sweep-source.v1"
SECTION, PATH, SWEEP = "SweepSection", "SweepPath", "OrdinarySweptBoss"
DRIVERS = ("section", "path")
PARAMETERS = ("section_radius_m", "path_radius_m", "edit_section_radius_m", "edit_path_radius_m")
PHASES = ("author", "section-edit", "section-reopen", "path-edit", "path-reopen")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_spec(spec):
    require(set(spec) == {"schema", "cohort", "density_kg_m3", "cases"}
            and spec["schema"] == SCHEMA and spec["cohort"] in ("disclosed", "heldout"),
            "unexpected native sweep source scope")
    density, cases = spec["density_kg_m3"], spec["cases"]
    require(type(density) in (int, float) and math.isfinite(density) and density > 0,
            "provide a positive document density in kg/m³")
    require(type(cases) is list and len(cases) == 2, "the source method requires two cases")
    for case in cases:
        require(type(case) is dict and set(case) == {"name", *PARAMETERS}
                and re.fullmatch("[A-Za-z][A-Za-z0-9]{1,39}", case["name"]),
                "unknown input field or case name")
        require(all(type(case[key]) in (int, float) and math.isfinite(case[key]) and case[key] >= 0.001
                    for key in PARAMETERS), "all sweep radii must be finite and at least one millimetre")
        section, path, edit_section, edit_path = (case[key] for key in PARAMETERS)
        require(max(section, edit_section) < min(path, edit_path) < 0.15
                and max(path, edit_path) <= 0.15 and section != edit_section and path != edit_path,
                "the two independent edits must keep the quarter tube regular and change their own radii")
    require(cases[0]["name"].casefold() != cases[1]["name"].casefold()
            and all(cases[0][key] != cases[1][key] for key in PARAMETERS),
            "the two sources must vary both initial values and both edit values")
    if spec["cohort"] == "heldout":
        require([case["name"] for case in cases] == ["Slot01", "Slot02"], "protected names must be ordered aliases")
    return density, cases


def dimensions(case, edit=None):
    require(edit in (None, *DRIVERS), "unknown single change")
    return (case["edit_section_radius_m" if edit == "section" else "section_radius_m"],
            case["edit_path_radius_m" if edit == "path" else "path_radius_m"])


def predict(case, density, edit=None):
    section, path = dimensions(case, edit)
    theta = math.pi / 2
    volume = math.pi * section**2 * path * theta
    area = 2 * math.pi * section * path * theta + 2 * math.pi * section**2
    transverse = (path + section**2 / (4 * path)) / theta
    return {
        "diameter_m": 2 * section,
        "arc_radius_m": path,
        "arc_length_m": theta * path,
        "path": {"center": [0.0, path, 0.0], "start": [0.0, 0.0, 0.0], "end": [path, path, 0.0]},
        "volume": volume,
        "area": area,
        "cap_area": math.pi * section**2,
        "com": [transverse, path - transverse, 0.0],
        "mass": density * volume,
        "bounds": [[0.0, -section, -section], [path + section, path, section]],
    }


def predictions(spec):
    density, cases = validate_spec(spec)
    return {case["name"]: {mode: predict(case, density, None if mode == "original" else mode)
                           for mode in ("original", *DRIVERS)}
            for case in cases}
