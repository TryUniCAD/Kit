from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import sys


LOCK_SHA256 = "99c3e345182c20853445bd7240a881d6fce22d397961779445961d61718a3298"
PROJECTION_SHA256 = "c18522a47dbc2848d6cc48b62b8172f49e8b8f5acd5314f4f9684839817a1b33"
NAMES = ("D00ScaledFront", "D01ScaledTop", "D02ScaledRight", "D03ScaledIsometric")


def digest(value):
    return sha256(value).hexdigest()


def checked(path, expected):
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError(f"digest changed: {path}")
    return data


def require(condition, message):
    if not condition:
        raise ValueError(message)


def axes(record):
    return [record[key] for key in "xyz"]


def matrix(record):
    return [record["f08"][f"m{index}"] for index in range(9)] if record["has_matrix"] else [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]


def multiply(rotation, point):
    return [sum(point[index] * rotation[index * 3 + axis] for index in range(3)) for axis in range(3)]


def transform(record):
    return {"matrix": matrix(record), "translation": [record[key] for key in ("f58", "f60", "f68")],
            "scale": record["f70"], "has_matrix": record["has_matrix"], "f78": record["f78"]}


def compare(name, actual, predicted):
    require(len(actual) == len(predicted), f"{name}: vector lengths differ")
    error = max((abs(left - right) for left, right in zip(actual, predicted, strict=True)), default=0.0)
    require(all(isclose(left, right, rel_tol=1e-12, abs_tol=1e-14) for left, right in zip(actual, predicted, strict=True)), f"{name}: formula differs")
    return {"matched": True, "max_absolute_error": error}


def audit(arguments):
    root = arguments.root.resolve()
    for path in (root, root / "src", root / "re/tooling/sw2026", root / "re/tooling/sw2026/serial"):
        sys.path.insert(0, str(path))
    from Classes import registry
    from CheckDrawingDefinitions import checked_artifacts, check_header, nodes, reencode
    from builders.Views import standard_views
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    directory = arguments.corpus.resolve()
    lock = json.loads(checked(directory / "SourceLock.json", LOCK_SHA256))
    projection = json.loads(checked(arguments.projection, PROJECTION_SHA256))
    require(lock["passed"] and lock["pinned_inputs_immutable"] and lock["control_results"] == [True, True]
            and lock["distinct_processes"] == 10 and lock["writer_output_count"] == 0, "unqualified native cohort")
    require(tuple(case["name"] for case in lock["cases"]) == NAMES and all(case["split"] == "discovery" for case in lock["cases"]), "source case disclosure differs")
    require(projection["source_lock_sha256"] == LOCK_SHA256 and projection["heldout_inputs_read"] == 0
            and all(case["definition"]["exact"] and case["header"]["exact"] for case in projection["cases"]), "projection custody differs")
    canonical = {row["o"]["f358"]: matrix(row["o"]["f368"]) for row in standard_views(detail_standard=1)}
    rules = registry()
    rows = []
    for case, prior in zip(lock["cases"], projection["cases"], strict=True):
        source, observed, reopened = checked_artifacts(directory, case)
        archive = SldprtArchive.from_bytes(source)
        definition = archive.require("Contents/Definition")
        header_bytes = archive.require("Header2")
        model, count = reencode(definition, rules, archive)
        header, header_count = check_header(header_bytes, rules)
        view, = [node for node in nodes(model["f1430"]) if node.cls == "moAbsoluteView"]
        require(prior["case"] == case["name"] and prior["source_sha256"] == digest(source), "prior case differs")
        support = nodes(view)
        require([node.cls for node in support] == ["moDetailFolder_c", "moRefPlane_c", "moProfileFeature_c", "moRefPlane_c", "moProfileFeature_c"], "support class order differs")
        sheet_plane, sheet_profile, model_plane, model_profile = support[1:]
        require(view["f7c8"] is sheet_profile and view["fde0"] is model_profile, "view support aliases differ")
        require(sheet_profile["pd_f78"]["ff8"] is sheet_plane and model_profile["pd_f78"]["ff8"] is model_plane, "profile plane aliases differ")
        position = axes(view["f778"])
        center = [view["f600"][f"b{index}"] for index in range(3)]
        scale = view["f780"] / view["f788"]
        rotation = canonical[view["f1018"]]
        rotated_center = multiply(rotation, center)
        sheet_data, model_data = sheet_plane["f6f8"], model_plane["f6f8"]
        require(sheet_data.cls == "moDrawingRefPlnData_c" and model_data.cls == "moAbsoluteRefPlnData_c", "support plane type differs")
        predictions = {"sheet_rotation": matrix({"has_matrix": 0}), "sheet_root": position,
                       "sheet_translation": [-value / scale for value in position], "sheet_scale": 1.0 / scale,
                       "model_rotation": rotation, "model_root": center, "model_scale": 1.0,
                       "model_translation": [-value for value in rotated_center],
                       "model_normal": [rotation[index] for index in (2, 5, 8)]}
        model_display = [center[axis] + model_data["b1"] * rotation[axis * 3] + model_data["b2"] * rotation[axis * 3 + 1] for axis in range(3)]
        predictions["model_display_origin"] = model_display
        checks = {}
        for role, data, profile in (("sheet", sheet_data, sheet_profile), ("model", model_data, model_profile)):
            for label, current in (("plane", data["f20"]), ("profile", profile["pd_ff0"])):
                checks[f"{role}_{label}_rotation"] = compare(role, matrix(current), predictions[f"{role}_rotation"])
                checks[f"{role}_{label}_translation"] = compare(role, transform(current)["translation"], predictions[f"{role}_translation"])
                checks[f"{role}_{label}_scale"] = compare(role, [current["f70"]], [predictions[f"{role}_scale"]])
            checks[f"{role}_root"] = compare(role, axes(data["root"]), predictions[f"{role}_root"])
        checks["sheet_normal"] = compare("sheet normal", axes(sheet_data["normal"]), [0.0, 0.0, 1.0])
        checks["sheet_display_origin"] = compare("sheet display origin", axes(sheet_plane["f6c0"]), [0.0, 0.0, 0.0])
        checks["sheet_rotation_state"] = compare("sheet rotation state", transform(sheet_data["f88"])["translation"] + [sheet_data["f88"]["f70"]], [0.0, 0.0, 0.0, 1.0])
        checks["model_normal"] = compare("model normal", axes(model_data["normal"]), predictions["model_normal"])
        checks["model_display_origin"] = compare("model display origin", axes(model_plane["f6c0"]), model_display)
        planar = sum(abs(value) >= 1e-8 for value in predictions["model_normal"]) == 1
        require(view["f610"] & 0x30 == (0x10 if planar else 0x20), "eligibility flag branch differs")
        require(all(node["f0c"] == 0 for node in support) and model_data["f20"]["f70"] == 1, "support flag/scale differs")
        require(view.get("fe60") is None, "alternate view owner is outside this support profile")
        rows.append({"case": case["name"], "orientation": view["f1018"], "scale": scale,
                     "source_sha256": digest(source), "source_bytes": len(source), "native_record_sha256": case["record_sha256"],
                     "definition": {"bytes": len(definition), "sha256": digest(definition), "map_next": count, "exact": True},
                     "header": {"bytes": len(header_bytes), "sha256": digest(header_bytes), "map_next": header_count, "exact": True},
                     "view_flags": {key: view[key] for key in ("f610", "f614", "f618", "f61c")},
                     "cached_2d_dimension_eligible": planar, "predictions": predictions, "formula_checks": checks,
                     "sheet_plane": {"class": sheet_data.cls, "root": axes(sheet_data["root"]), "normal": axes(sheet_data["normal"]),
                                     "transform": transform(sheet_data["f20"]), "profile_transform": transform(sheet_profile["pd_ff0"]),
                                     "display_origin": axes(sheet_plane["f6c0"]), "rectangle": [sheet_data[f"b{index}"] for index in range(4)]},
                     "model_plane": {"class": model_data.cls, "root": axes(model_data["root"]), "normal": axes(model_data["normal"]),
                                     "transform": transform(model_data["f20"]), "profile_transform": transform(model_profile["pd_ff0"]),
                                     "display_origin": axes(model_plane["f6c0"]), "rectangle": [model_data[f"b{index}"] for index in range(4)]},
                     "support_ids": [node["f08"] for node in support], "support_feature_flags": [node["f0c"] for node in support],
                     "aliases_exact": True, "inputs_immutable": True})
        checked(directory / case["name"] / "author" / (case["name"] + ".SLDDRW"), case["native_sha256"])
    return {"schema": "kit.sw2026.disclosed-drawing-support-comparison.v1", "source_lock_sha256": LOCK_SHA256,
            "projection_fields_sha256": PROJECTION_SHA256, "script_sha256": digest(Path(__file__).read_bytes()), "cases": rows,
            "exact_stream_roundtrips": 8, "formula_check_groups": sum(len(row["formula_checks"]) for row in rows),
            "heldout_inputs_read": 0, "writer_outputs": 0, "vendor_runtime_executed": False,
            "native_writer_acceptance": False, "scope": "four disclosed ordinary resolved rectangular one-view discovery sources only"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    require(not arguments.output.exists(), "choose an unused research receipt")
    receipt = audit(arguments)
    arguments.output.write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(arguments.output), "sha256": digest(arguments.output.read_bytes()),
                      "exact_stream_roundtrips": receipt["exact_stream_roundtrips"], "formula_check_groups": receipt["formula_check_groups"]}))


if __name__ == "__main__":
    main()
