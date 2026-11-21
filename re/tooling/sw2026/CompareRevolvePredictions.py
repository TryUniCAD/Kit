from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PrepareRevolvePredictions import SOURCE_LOCK, digest, write_value


def read_json(path, expected=None):
    encoded = path.read_bytes()
    if expected is not None and digest(encoded) != expected:
        raise ValueError(f"record hash differs: {path.name}")
    return json.loads(encoded)


def close(actual, expected, absolute=1e-12):
    return type(actual) in (int, float) and math.isclose(actual, expected, rel_tol=2e-7, abs_tol=absolute)


def vector(actual, expected, absolute=1e-10):
    return isinstance(actual, list) and len(actual) == len(expected) and all(
        close(value, target, absolute) for value, target in zip(actual, expected, strict=True)
    )


def same_mass(actual, expected):
    return (
        close(actual.get("volume"), expected["volume"], 0)
        and close(actual.get("area"), expected["area"], 0)
        and vector(actual.get("com"), expected["com"])
    )


def tree(features):
    return [tuple(feature.get(name) for name in ("name", "type", "error", "warning", "suppressed")) for feature in features]


def compare_profile(profile, request, targets):
    frames = profile.get("frame_points", [])
    frames_match = len(frames) == 4 and all(
        vector(point, target) for point, target in zip(frames, targets["frame_points"], strict=True)
    )
    vertices = request["vertices_m"]
    expected = [(first, second, False) for first, second in zip(vertices, vertices[1:] + vertices[:1], strict=True)]
    expected.append((request["axis_start_m"], request["axis_end_m"], True))
    remaining = profile.get("segments", [])[:]
    for start, end, construction in expected:
        indices = [
            index for index, item in enumerate(remaining) if item.get("construction") is construction and
            ((vector(item.get("start"), start) and vector(item.get("end"), end)) or
             (vector(item.get("start"), end) and vector(item.get("end"), start)))
        ]
        if len(indices) != 1:
            return False
        remaining.pop(indices[0])
    return not remaining and frames_match and profile.get("configuration") == targets["configuration"]


def dimension(observation, document, expected):
    wanted = f"D1@OrdinaryBossRevolve@{document}.Part"
    entries = [
        item for feature in observation.get("features", []) if feature["type"] == "Revolution"
        for item in feature.get("dims", [])
    ]
    return len(entries) == 1 and entries[0]["name"] == wanted and close(entries[0]["value"], expected)


def compare_phase(observation, source, target, profile, request, candidate_name, source_name):
    return {
        "geometry_matches_prediction": observation.get("bodies") == target["bodies"] and same_mass(observation.get("mass", {}), target),
        "geometry_matches_locked_source": observation.get("bodies") == source["bodies"] and same_mass(observation.get("mass", {}), source["mass"]),
        "same_ordered_tree": tree(observation.get("features", [])) == tree(source["features"]),
        "same_driving_dimension": (
            dimension(observation, candidate_name, target["angle_radians"])
            and dimension(source, source_name, target["angle_radians"])
        ),
        "same_profile_and_frame": compare_profile(observation.get("profile", {}), request, profile),
        "same_axis_direction_and_angle": (
            observation.get("forward_handedness") == source["forward_handedness"]
            and observation.get("reverse") == source["reverse"]
            and close(observation.get("angle_radians"), target["angle_radians"])
            and observation.get("parents") == source["parents"]
        ),
    }


def compare_case(prediction, generated, saved, reference, profile, request):
    old_name, new_name = prediction["source_case"], prediction["model"]["name"]
    initial = generated.get("before_explicit_rebuild", {})
    startup = {
        "native_open_clean": generated.get("open_status") == {"opened": True, "errors": 0, "warnings": 0},
        "one_body_available_on_open": initial.get("bodies") == 1,
        "native_tree_available_on_open": tree(initial.get("features", [])) == tree(reference["reopened"]["features"]),
        "no_initial_rebuild_diagnostics": initial.get("whats_wrong") == 0,
    }
    edit = generated.get("edit", {})
    acceptance = {
        "initial": startup,
        "rebuilt": compare_phase(generated.get("reopened", {}), reference["reopened"], profile["original"], profile, request, new_name, old_name),
        "edited": compare_phase(generated.get("edited", {}), reference["edited"], profile["edited"], profile, request, new_name, old_name),
        "edited_reopen": compare_phase(saved.get("reopened", {}), reference["edited"], profile["edited"], profile, request, new_name, old_name),
        "edit_and_save": {
            "edit_passed": edit.get("passed") is True and edit.get("name") == f"D1@OrdinaryBossRevolve@{new_name}.Part",
            "native_save_clean": generated.get("edited_derivative", {}).get("save_status") == [True, 0, 0],
            "native_saved_reopen_clean": saved.get("open_status") == {"opened": True, "errors": 0, "warnings": 0},
            "display_preference_restored": generated.get("display_dimension_preference", {}).get("restored") is True,
        },
    }
    return {
        "name": old_name, "candidate_sha256": prediction["sha256"], "checks": acceptance,
        "passed": all(all(row.values()) for row in acceptance.values()),
    }


def main():
    parser = argparse.ArgumentParser(description="Compare frozen revolve predictions with independently locked native sources")
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--predictions-sha256", required=True)
    parser.add_argument("--source-lock", required=True, type=Path)
    parser.add_argument("--reference-root", required=True, type=Path)
    parser.add_argument("--inspection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = read_json(args.predictions / "Predictions.json", args.predictions_sha256)
    lock = read_json(args.source_lock, SOURCE_LOCK)
    locked = {entry["name"]: entry for entry in lock["cases"] if entry["split"] == manifest["split"]}
    predicted = manifest["predictions"]
    if manifest["source_lock_sha256"] != SOURCE_LOCK or [row["source_case"] for row in predicted] != list(locked):
        raise ValueError("prediction cohort differs from the source lock")
    requests = []
    for entry in predicted:
        name = entry["model"]["name"]
        if digest((args.predictions / (name + ".SLDPRT")).read_bytes()) != entry["sha256"]:
            raise ValueError("generated bytes changed after prediction")
        request = read_json(args.predictions / (name + ".request.json"), entry["request_sha256"])
        profile = read_json(args.predictions / (name + ".targets.json"), entry["targets_sha256"])
        read_json(args.predictions / (name + ".archive.json"), entry["generator_receipt_sha256"])
        requests.append((request["document"], profile))
    batch = read_json(args.inspection / "Inspection.json")
    if not batch["controls_healthy"] or batch["distinct_processes"] != 2 + 2 * len(predicted):
        raise ValueError("native comparison requires both healthy controls and distinct process identities")
    if not batch["inspect_profile"] or not batch["inspect_before_rebuild"]:
        raise ValueError("native batch did not record initial tree and sketch geometry")
    results = []
    for entry, (request, profile) in zip(predicted, requests, strict=True):
        name, source_name = entry["model"]["name"], entry["source_case"]
        generated = next(row for row in batch["cases"] if row["job"]["case"]["name"] == name)
        saved = next(row for row in batch["derivative_reopens"] if row["job"]["case"]["name"] == name)
        read_json(args.inspection / (name + ".reopen.json"), generated["phase_sha256"])
        read_json(args.inspection / (name + ".edited-reopen.json"), saved["phase_sha256"])
        if not generated["passed"] or not saved["passed"] or generated["source_sha256"] != entry["sha256"]:
            raise ValueError(f"native candidate did not pass open, edit and save: {name}")
        raw = args.reference_root / manifest["split"] / source_name
        source_row = locked[source_name]
        if digest((raw / (source_name + ".SLDPRT")).read_bytes()) != source_row["native_sha256"]:
            raise ValueError("locked native source bytes differ")
        reference = read_json(raw / (source_name + ".reopen.json"), source_row["phase_record_sha256"][1])
        if not reference["passed"] or not reference.get("edit", {}).get("passed"):
            raise ValueError("locked source did not pass its independent edit")
        result = compare_case(entry, generated, saved, reference, profile, request)
        result.update(reference_sha256=source_row["native_sha256"], reference_phase_sha256=source_row["phase_record_sha256"][1])
        results.append(result)
    passed = all(row["passed"] for row in results)
    checksum = write_value(args.output, {
        "schema": "kit.sw2026.ordinary-revolve-comparison.v1", "split": manifest["split"],
        "predictions_sha256": args.predictions_sha256, "source_lock_sha256": SOURCE_LOCK,
        "inspection_sha256": digest((args.inspection / "Inspection.json").read_bytes()),
        "distinct_processes": batch["distinct_processes"], "controls_healthy": batch["controls_healthy"],
        "cases": results, "passed": passed, "heldout_acceptance": passed and manifest["split"] == "heldout",
        "accepted_production_parts": 0,
    })
    print(json.dumps({"passed": passed, "comparison_sha256": checksum, "cases": len(results)}))
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())
