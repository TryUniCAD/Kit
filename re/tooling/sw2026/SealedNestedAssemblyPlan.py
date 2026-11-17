from __future__ import annotations

from collections import Counter
from copy import deepcopy
import math
from pathlib import PureWindowsPath

from AuthorCurves import require
from NestedAssemblySourcePlan import HEIGHT, PARAMETERS, WIDTH, expected_tree, part_geometry, placement_matrix, validate_case


SCHEMA = "kit.sw2026.sealed-nested-prism-prediction.v1"


def authored_part(name, depth, output):
    from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput

    left, right, bottom, top = -WIDTH / 2, WIDTH / 2, -HEIGHT / 2, HEIGHT / 2
    request = MakePartInput([[left, bottom], [right, bottom], [right, top], [left, top]], depth, name)
    request["document"].update(configuration_name="Default", rectangle_dimensions={
        "width_text_m": [0.0, bottom - HEIGHT / 2], "height_text_m": [right + HEIGHT / 2, 0.0], "route_centerline": False,
    })
    request["output"] = {"path_name": str(output), "saved_at": request["provenance"]["modified_at"] + 51}
    return request


def authored_assembly(name, output):
    from tests.Convert.Solidworks.Research.Assembly.RootRequest import RootRequest

    request = RootRequest(name, 0.3)
    request["output"] = {"path_name": str(output), "saved_at": request["provenance"]["modified_at"] + 51}
    return request


def occurrence_names(rows):
    counts = Counter()
    result = []
    for row in rows:
        target = row["target"]
        counts[target] += 1
        result.append(f"{target}-{counts[target]}")
    return result


def source_request(case, working):
    validate_case(case)
    working = PureWindowsPath(working)
    require(working.is_absolute() and working.drive and not working.drive.startswith("\\\\") and ".." not in working.parts,
            "sealed neutral requests require an absolute guest-local working directory")
    definitions = [{"id": row["name"], "kind": "part", "request": authored_part(row["name"], row["depth_m"], working / (row["name"] + ".SLDPRT"))}
                   for row in case["parts"]]
    for assembly in case["assemblies"]:
        rows = []
        for entry, name in zip(assembly["occurrences"], occurrence_names(assembly["occurrences"]), strict=True):
            pose = placement_matrix(entry["placement"])
            rows.append({"target": entry["target"], "name": name, "placement": {"origin": pose[9:12], "u": pose[:3], "v": pose[3:6]}})
        name = assembly["name"]
        definitions.append({"id": name, "kind": "assembly", "request": authored_assembly(name, working / (name + ".SLDASM")), "occurrences": rows})
    return {"root": case["assemblies"][-1]["name"], "definitions": definitions}


def source_prediction(case):
    validate_case(case)
    definitions = {}
    assemblies = {row["name"]: row["occurrences"] for row in case["assemblies"]}

    def named_tree(owner, edited):
        shape = expected_tree(case, owner=owner, edited=edited)

        def name_rows(rows, parent):
            names = occurrence_names(assemblies[parent])
            for row, name in zip(rows, names, strict=True):
                row["name"] = name
                if row["children"]:
                    name_rows(row["children"], row["target"])

        name_rows(shape["children"], owner)
        return shape

    for part in case["parts"]:
        name, original = part["name"], part["depth_m"]
        changed = case["edit"]["depth_m"] if name == case["edit"]["part"] else original

        def prism(depth):
            return part_geometry(depth) | {"children": [], "total_occurrences": 0,
                                           "dimensions_m": dict(zip(PARAMETERS, (WIDTH, HEIGHT, depth), strict=True))}

        definitions[name] = {"kind": "part", "file": name + ".SLDPRT", "configuration": "Default", "initial": prism(original), "edited": prism(changed)}
    for name in assemblies:
        definitions[name] = {"kind": "assembly", "file": name + ".SLDASM", "configuration": "Default",
                             "initial": named_tree(name, False), "edited": named_tree(name, True)}
    return {"schema": SCHEMA, "root": case["assemblies"][-1]["name"], "edit": deepcopy(case["edit"]), "definitions": definitions}


def source_semantics(case, snapshot, prediction):
    from AuthorNestedAssemblySources import match_geometry
    from NestedAssemblySourcePlan import matches_transform

    require(snapshot["case"] == case, "sealed source snapshot does not match its locked neutral specification")
    source = snapshot["result"]["restored"]
    root = prediction["root"]
    wanted = prediction["definitions"][root]["initial"]
    require(source["total_occurrences"] == wanted["total_occurrences"] and source["body_count"] == wanted["body_count"],
            "sealed source hierarchy does not match its independent prediction")

    def visit(actual, expected, prefix=""):
        require(len(actual) == len(expected), "sealed source immediate hierarchy differs")
        for row, spec in zip(actual, expected, strict=True):
            name = prefix + spec["name"]
            require(row["name"] == name and row["target"] == spec["target"] and row["kind"] == spec["kind"] and row["fixed"] is False and row["configuration"] == "Default" and
                    matches_transform(row["world"], spec["world"]), "sealed source requires occurrence semantics outside the declared writer profile")
            visit(row["children"], spec["children"], name + "/")

    visit(source["occurrences"], wanted["children"])
    require(set(source["definitions"]) == set(prediction["definitions"]), "sealed source semantic dependency closure differs")
    for name, row in source["definitions"].items():
        shape = prediction["definitions"][name]["initial"]
        match_geometry(row["mass_properties"], shape)
        if "dimensions_m" in shape:
            require(set(row["dimensions_m"]) == set(shape["dimensions_m"]) and all(
                math.isclose(row["dimensions_m"][key], value, rel_tol=0, abs_tol=1e-12) for key, value in shape["dimensions_m"].items()),
                "sealed source driving dimensions differ from its semantic specification")
    return True
