from __future__ import annotations

import copy
import hashlib
import json
import math
import struct
from pathlib import Path


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(values, size):
    require(
        isinstance(values, list) and len(values) == size, "numeric array length differs"
    )
    require(
        all(type(value) in (int, float) and math.isfinite(value) for value in values),
        "nonfinite numeric evidence",
    )
    return values


def neutral_metrics(model):
    require(
        model["plane_axis"] == "z",
        "this independent baseline requires the declared z plane",
    )
    points = model["vertices_m"]
    require(len(points) >= 3, "neutral polygon is incomplete")
    for point in points:
        finite(point, 2)
    depth, density = model["depth_m"], model["density_kg_m3"]
    finite([depth, density], 2)
    require(depth > 0 and density > 0, "depth and density must be positive")
    pairs = list(zip(points, points[1:] + points[:1]))
    crosses = [left[0] * right[1] - right[0] * left[1] for left, right in pairs]
    signed = math.fsum(crosses)
    require(signed != 0, "neutral polygon area is zero")
    area = abs(signed) / 2
    perimeter = math.fsum(
        math.hypot(right[0] - left[0], right[1] - left[1]) for left, right in pairs
    )
    centroid = [
        math.fsum(
            (left[axis] + right[axis]) * cross
            for (left, right), cross in zip(pairs, crosses)
        )
        / (3 * signed)
        for axis in (0, 1)
    ]
    volume = area * depth
    return {
        "bodies": 1,
        "volume": volume,
        "area": 2 * area + perimeter * depth,
        "com": [*centroid, depth / 2],
        "mass": volume * density,
    }


def compare(actual, expected, absolute, relative=1e-9):
    finite([actual, expected], 2)
    difference = abs(actual - expected)
    tolerance = max(absolute, relative * abs(expected))
    return {
        "actual": actual,
        "expected": expected,
        "absolute_error": difference,
        "relative_error": difference / abs(expected) if expected else None,
        "tolerance": tolerance,
        "within_tolerance": difference <= tolerance,
    }


def metric_comparisons(actual, expected):
    result = {
        "volume_m3": compare(actual["volume"], expected["volume"], 1e-15),
        "surface_area_m2": compare(actual["area"], expected["area"], 1e-12),
    }
    if "mass" in expected:
        result["mass_kg"] = compare(actual["mass"], expected["mass"], 1e-15)
    finite(actual["com"], 3)
    finite(expected["com"], 3)
    result.update(
        {
            f"center_of_mass_{axis}_m": compare(
                actual["com"][axis], expected["com"][axis], 1e-12
            )
            for axis in range(3)
        }
    )
    require(
        all(value["within_tolerance"] for value in result.values()),
        "native metrics differ from independent expectations",
    )
    return result


def depth_readback(row, parameter):
    values = [
        dimension
        for feature in row["features"]
        for dimension in feature.get("dims", [])
        if dimension["name"].split("@")[:2] == parameter.split("@")[:2]
    ]
    require(len(values) == 1, "driving depth readback is not unique")
    finite([values[0]["value"]], 1)
    return values[0]


def native_status(row, feature_count, require_problem_count):
    identity = row["oracle_identity"]
    features = row["features"]
    finite([row["mass"]["volume"], row["mass"]["area"], row["mass"]["mass"]], 3)
    finite(row["mass"]["com"], 3)
    status = {
        "opened": row.get("opened") is True,
        "zero_open_errors": row.get("open_errors") == 0,
        "zero_open_warnings": row.get("open_warnings") == 0,
        "rebuilt": row.get("rebuilt") is True,
        "one_body": row.get("bodies") == 1,
        "expected_feature_count": len(features) == feature_count,
        "features_clean_and_unsuppressed": bool(features)
        and all(
            feature.get("error") == 0
            and feature.get("warning") is False
            and feature.get("suppressed") is False
            for feature in features
        ),
        "no_diagnostics_or_dialogs": all(
            row.get(key, []) == []
            for key in (
                "session_diagnostics",
                "controller_diagnostics",
                "dialogs",
                "progress_windows",
            )
        ),
        "no_recorded_exception_or_cleanup_failure": not any(
            row.get(key)
            for key in ("exception", "failure_stage", "cleanup_error", "cleanup_errors")
        ),
        "exact_observed_2026_identity": identity["version_matches"] is True
        and identity["file_version"] == "34.5.2.0604"
        and identity["file_version_words"] == [34, 5, 2, 604]
        and identity["sha256"]
        == "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe",
    }
    if require_problem_count:
        status["zero_whats_wrong"] = row.get("whats_wrong") == 0
    require(
        type(identity["process_creation_filetime"]) is int,
        "process birth identity was rounded",
    )
    require(all(status.values()), "native document status failed")
    return {
        "checks": status,
        "passed": True,
        "whats_wrong_recorded": "whats_wrong" in row,
        "whats_wrong": row.get("whats_wrong"),
    }


def tree(row):
    return [
        {"name": feature["name"], "type": feature["type"]}
        for feature in row["features"]
    ]


def tree_changes(before, after):
    require(len(before) == len(after) == 20, "candidate feature counts differ")
    return [
        {"index": index, "before": left, "after": right}
        for index, (left, right) in enumerate(zip(before, after))
        if left != right
    ]


def maximum_errors(rows):
    result = {}
    for group in ("volume_m3", "surface_area_m2", "mass_kg", "center_of_mass_m"):
        selected = [
            item
            for item in rows
            if item["metric"] == group
            or group == "center_of_mass_m"
            and item["metric"].startswith("center_of_mass_")
        ]
        result[group] = {
            "count": len(selected),
            "max_absolute": max(selected, key=lambda value: value["absolute_error"]),
            "max_relative": max(
                (item for item in selected if item["relative_error"] is not None),
                key=lambda value: value["relative_error"],
            ),
        }
    return result


def analyze(directory):
    provenance = load(directory / "Provenance.json")
    view = load(directory / "NativeViewReport.json")
    edit = load(directory / "EditReport.json")
    edit_job = load(directory / "EditJob.json")
    view_job = load(directory / "ViewJob.json")
    baselines = {
        item["name"]: item for item in load(directory / "BaselineInputs.json")["cases"]
    }
    image_manifest = load(directory / "ImageManifest.json")
    sources = {
        item["name"].removesuffix(".SLDPRT"): item["sha256"]
        for item in provenance["generated_input_manifest"]
    }
    tools = load(directory / "FrozenTools.json")["files"]
    require(
        view["job_sha256"] == provenance["raw_sources"]["ViewJob.json"]["sha256"],
        "view job fingerprint differs",
    )
    require(
        edit["job_sha256"] == provenance["raw_sources"]["EditJob.json"]["sha256"],
        "edit job fingerprint differs",
    )
    require(
        view["inspector_sha256"] == tools["InspectView.py"]["sha256"]
        and edit["inspector_sha256"] == tools["InspectEdit.py"]["sha256"],
        "inspector hashes differ from frozen tools",
    )
    require(
        [(row["name"], row["kind"]) for row in view["results"]]
        == [(row["name"], row["kind"]) for row in view_job["cases"]]
        == [(row["name"], row["kind"]) for row in provenance["case_order"]],
        "view row order differs from job",
    )
    controls = [row for row in view["results"] if row["kind"] == "control"]
    require(
        len(view["results"]) == 5
        and len(controls) == 2
        and view["results"][0] is controls[0]
        and view["results"][-1] is controls[-1],
        "view controls do not bracket candidates",
    )
    control_arrays = [
        row["rotations_" + phase]["standard"]
        for row in controls
        for phase in ("before", "after")
    ]
    metrics_rows, native_rows, array_rows, view_rows, edit_rows = [], [], [], [], []
    for row in view["results"]:
        native_rows.append(row)
        candidate = row["name"] in sources
        status = native_status(row, 20 if candidate else 19, False)
        expected_sha = (
            sources[row["name"]] if candidate else provenance["original_control_sha256"]
        )
        require(
            row["sha256"] == row["sha256_after"] == expected_sha
            and row["unchanged_input"] is True,
            "view input changed or differs from staged bytes",
        )
        require(
            row["stage"] == "capture_return"
            and row["initial_bitmap_saved"]
            and row["bitmap_saved"],
            "view capture did not complete",
        )
        for phase in ("before", "after"):
            rotations = row["rotations_" + phase]
            require(
                set(rotations["standard"]) == {str(index) for index in range(1, 10)},
                "standard view inventory differs",
            )
            finite(rotations["active"], 16)
            for view_id, values in rotations["standard"].items():
                finite(values, 9)
                discrepancy = max(
                    abs(value - target)
                    for anchor in control_arrays
                    for value, target in zip(values, finite(anchor[view_id], 9))
                )
                require(discrepancy <= 1e-12, "standard view differs from controls")
                array_rows.append(
                    {
                        "case": row["name"],
                        "phase": phase,
                        "view_id": view_id,
                        "coefficient_count": 9,
                        "maximum_absolute_difference_against_all_four_control_anchors": discrepancy,
                        "within_declared_absolute_tolerance": True,
                    }
                )
        selected_delta = max(
            abs(left - right)
            for left, right in zip(
                row["rotations_after"]["active"][:9],
                row["rotations_after"]["standard"]["7"],
            )
        )
        require(
            selected_delta <= 1e-12,
            "selected active rotation differs from own standard view 7",
        )
        initial_delta = max(
            abs(left - right)
            for control in controls
            for left, right in zip(
                row["rotations_before"]["active"][:9],
                control["rotations_before"]["active"][:9],
            )
        )
        result = {
            "name": row["name"],
            "source_sha256": row["sha256"],
            "native_status": status,
            "feature_count": len(row["features"]),
            "selected_active_rotation_vs_own_view7_max_absolute_difference": selected_delta,
            "initial_active_rotation_vs_controls_max_absolute_difference": initial_delta,
        }
        if candidate:
            neutral = baselines[row["name"]]["neutral_input"]
            expected = neutral_metrics(neutral)
            comparisons = metric_comparisons(row["mass"], expected)
            result["independent_neutral_comparison"] = comparisons
            result["prior_independent_baseline_comparison"] = metric_comparisons(
                row["mass"], baselines[row["name"]]["expected_baseline"]
            )
            result["driving_depth_readback"] = depth_readback(
                row, "D1@" + neutral["extrusion_name"]
            )
            result["depth_comparison"] = compare(
                result["driving_depth_readback"]["value"], neutral["depth_m"], 1e-12, 0
            )
            require(
                result["depth_comparison"]["within_tolerance"],
                "view depth differs from neutral input",
            )
            metrics_rows.extend(
                {"case": row["name"], "phase": "view", "metric": key, **value}
                for key, value in comparisons.items()
            )
        view_rows.append(result)
    require(len(array_rows) == 90, "standard array count differs")
    require(
        controls[0]["mass"] == controls[1]["mass"], "view control measurements differ"
    )
    edit_controls = []
    for label in ("control_before", "control_after"):
        row = edit[label]
        native_rows.append(row)
        require(
            row["sha256"] == provenance["original_control_sha256"],
            "edit control fingerprint differs",
        )
        edit_controls.append(
            {
                "phase": label,
                "native_status": native_status(row, 19, True),
                "mass": row["mass"],
            }
        )
    require(
        edit["controls_healthy"] is True
        and edit["geometry_edit_reopen_passed"] is True,
        "native edit batch did not pass",
    )
    require(
        edit["control_before"]["mass"]
        == edit["control_after"]["mass"]
        == controls[0]["mass"],
        "control mass properties differ across batches",
    )
    require(
        [row["name"] for row in edit["cases"]]
        == [row["name"] for row in edit_job["cases"]]
        == list(baselines),
        "edit case inventory differs",
    )
    for recorded, request in zip(edit["cases"], edit_job["cases"]):
        name = recorded["name"]
        neutral = baselines[name]["neutral_input"]
        require(
            request["neutral_input"] == neutral,
            "job neutral inputs differ from independent publication",
        )
        changed = copy.deepcopy(neutral)
        changed["depth_m"] = request["value_m"]
        require(
            request["value_m"] / neutral["depth_m"] == 1.25, "unexpected depth factor"
        )
        require(
            recorded["unchanged_source"] is True
            and recorded["source_sha256_before"]
            == recorded["source_sha256_after"]
            == sources[name],
            "edit source changed",
        )
        require(
            all(
                recorded[key] is True
                for key in ("baseline_match", "edit_match", "reopen_match")
            ),
            "native metric match flag failed",
        )
        phases = {}
        for phase in ("baseline", "edit", "reopened"):
            row = recorded[phase]
            native_rows.append(row)
            model = neutral if phase == "baseline" else changed
            comparisons = metric_comparisons(row["mass"], neutral_metrics(model))
            actual_depth = depth_readback(row, request["parameter"])
            depth = compare(actual_depth["value"], model["depth_m"], 1e-12, 0)
            require(depth["within_tolerance"], "edit depth readback differs")
            phases[phase] = {
                "native_status": native_status(row, 20, True),
                "source_or_copy_sha256": row.get(
                    "sha256", row.get("edited_copy_sha256")
                ),
                "feature_count": len(row["features"]),
                "independent_neutral_comparison": comparisons,
                "job_expected_comparison": metric_comparisons(
                    row["mass"],
                    request["expected"]["before" if phase == "baseline" else "after"],
                ),
                "depth_readback": actual_depth,
                "depth_comparison": depth,
            }
            metrics_rows.extend(
                {"case": name, "phase": phase, "metric": key, **value}
                for key, value in comparisons.items()
            )
        saved = recorded["edit"]
        require(
            saved["saved"] is True
            and saved["save_errors"] == saved["save_warnings"] == 0,
            "edited copy did not save cleanly",
        )
        require(
            saved["parameter"] == request["parameter"]
            and saved["original_value_m"] == neutral["depth_m"]
            and saved["requested_value_m"]
            == saved["readback_value_m"]
            == request["value_m"],
            "edit setter/readback differs from requested depth",
        )
        require(
            saved["edited_copy_sha256"] == recorded["reopened"]["sha256"],
            "saved copy differs from fresh reopen input",
        )
        before = tree(recorded["baseline"])
        live_changes = tree_changes(before, tree(saved))
        reopen_changes = tree_changes(before, tree(recorded["reopened"]))
        require(live_changes == [], "live edit changed feature names or type order")
        require(
            reopen_changes
            == [
                {
                    "index": 12,
                    "before": {"name": "authored material", "type": "MaterialFolder"},
                    "after": {
                        "name": "Material <not specified>",
                        "type": "MaterialFolder",
                    },
                }
            ],
            "fresh reopen tree change differs from measured folder normalization",
        )
        type_order = [item["type"] for item in before]
        require(
            all(
                [item["type"] for item in tree(recorded[phase])] == type_order
                for phase in ("edit", "reopened")
            ),
            "feature type order differs",
        )
        factor = (
            recorded["edit"]["mass"]["volume"] / recorded["baseline"]["mass"]["volume"]
        )
        factor_comparison = compare(factor, 1.25, 1e-12, 0)
        require(
            factor_comparison["within_tolerance"],
            "volume does not follow the requested depth factor",
        )
        edit_rows.append(
            {
                "name": name,
                "source_sha256": sources[name],
                "edited_copy_sha256": saved["edited_copy_sha256"],
                "source_unchanged": True,
                "saved_copy_fingerprint_matches_fresh_reopen": True,
                "saved_without_errors_or_warnings": True,
                "native_match_flags": {
                    key: recorded[key]
                    for key in ("baseline_match", "edit_match", "reopen_match")
                },
                "phases": phases,
                "depth_factor": 1.25,
                "measured_volume_factor": factor_comparison,
                "live_edit_feature_name_and_type_order_preserved": True,
                "feature_type_order_preserved_through_reopen": True,
                "full_feature_names_preserved_through_reopen": False,
                "live_edit_tree_changes": live_changes,
                "fresh_reopen_tree_changes": reopen_changes,
                "bounded_geometry_depth_save_reopen_passed": True,
            }
        )
    image_results = []
    by_name = {row["name"]: row for row in view["results"]}
    for item in image_manifest["images"]:
        png = item["published_png"]
        data = (directory / png["path"]).read_bytes()
        require(
            data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR",
            "published image is not PNG",
        )
        require(
            hashlib.sha256(data).hexdigest() == png["sha256"]
            and len(data) == png["bytes"]
            and list(struct.unpack(">II", data[16:24]))
            == [png["width"], png["height"]],
            "PNG changed or its metadata differs",
        )
        key = "initial_bitmap" if item["phase"] == "initial" else "bitmap"
        require(
            item["native_bmp"]["sha256"] == by_name[item["case"]][key + "_sha256"]
            and item["native_bmp"]["bytes"] == by_name[item["case"]][key + "_bytes"],
            "conversion fingerprint differs from native image receipt",
        )
        image_results.append(
            {
                "case": item["case"],
                "phase": item["phase"],
                "png": png["path"],
                "sha256": png["sha256"],
                "dimensions": [png["width"], png["height"]],
                "copied_bytes_and_native_bmp_receipts_match": True,
            }
        )
    lifetimes = [
        (
            row["oracle_identity"]["process_id"],
            row["oracle_identity"]["process_creation_filetime"],
        )
        for row in native_rows
    ]
    require(
        len(lifetimes) == len(set(lifetimes)) == 16,
        "native snapshots do not have distinct process lifetimes",
    )
    require(len(metrics_rows) == 72, "independent metric comparison count differs")
    owner_verification = load(directory / "RootPosthocVerification.json")
    require(
        len(owner_verification["phases"]) == 9
        and all(item["clean"] for item in owner_verification["phases"]),
        "independent owner phase verification differs",
    )
    maxima = maximum_errors(metrics_rows)
    owner_maxima = owner_verification["maxima"]
    require(
        owner_maxima["volume_relative"]
        == maxima["volume_m3"]["max_relative"]["relative_error"]
        and owner_maxima["mass_relative"]
        == maxima["mass_kg"]["max_relative"]["relative_error"]
        and owner_maxima["area_relative"]
        == maxima["surface_area_m2"]["max_relative"]["relative_error"]
        and owner_maxima["com_absolute_m"]
        == maxima["center_of_mass_m"]["max_absolute"]["absolute_error"],
        "independent owner maxima differ",
    )
    inputs = [
        "NativeViewReport.json",
        "EditReport.json",
        "ViewJob.json",
        "EditJob.json",
        "SourceManifest4ed.json",
        "Artifact8d.json",
        "JobPreparation.json",
        "PngConversion.json",
        "BaselineInputs.json",
        "ImageManifest.json",
        "FrozenTools.json",
        "HostReports.json",
        "Provenance.json",
        "RootPosthocVerification.json",
        "Analyze.py",
    ]
    return {
        "schema": "kit-sw2026-canonical-polygon-analysis/1",
        "authority": "independent standard-library JSON arithmetic over completed oracle records, neutral polygon inputs and unchanged PNG bytes; no product or oracle execution",
        "independent_owner_verification": {
            "record": "RootPosthocVerification.json",
            "recorded_at": owner_verification["recorded_at"],
            "all_nine_candidate_phases_clean": True,
            "neutral_metric_maxima_agree": True,
            "full_feature_name_parity": owner_verification["full_feature_name_parity"],
        },
        "analysis_input_sha256": {name: digest(directory / name) for name in inputs},
        "staged_source_revision": provenance["staged_source_revision"],
        "byte_identical_verified_artifact_head": provenance[
            "current_artifact_root_verified"
        ]["head"],
        "counts": {
            "view_rows": 5,
            "view_controls": 2,
            "edit_controls": 2,
            "candidate_baseline_edit_reopen_snapshots": 9,
            "standard_view_arrays": 90,
            "standard_coefficients": 810,
            "standard_coefficients_against_four_control_anchors": 3240,
            "finite_active_transforms_of_length16": 10,
            "png_images": len(image_results),
            "distinct_native_process_lifetimes": len(set(lifetimes)),
            "independent_candidate_metric_comparisons": len(metrics_rows),
        },
        "tolerances": {
            "relative_geometry": 1e-9,
            "volume_absolute_m3": 1e-15,
            "area_absolute_m2": 1e-12,
            "com_absolute_m": 1e-12,
            "mass_absolute_kg": 1e-15,
            "depth_absolute_m": 1e-12,
            "rotation_coefficient_absolute": 1e-12,
            "formula": "abs(actual-expected) <= max(absolute tolerance, relative tolerance*abs(expected)); rotation and depth use absolute tolerance only",
        },
        "neutral_derivation": {
            "source": "preexisting independently published BaselineInputs.json and matching unchanged neutral EditJob inputs",
            "planar_area": "abs(sum(x_i*y_next-x_next*y_i))/2",
            "centroid": "sum((coordinate_i+coordinate_next)*cross_i)/(3*sum(cross_i))",
            "perimeter": "sum(hypot(dx,dy))",
            "volume": "planar_area*depth",
            "surface_area": "2*planar_area+perimeter*depth",
            "center_of_mass": "polygon centroid x and y, depth/2",
            "mass": "density*volume",
            "native_payload_inspection": False,
        },
        "controls_healthy_in_both_batches": True,
        "control_mass_properties_identical_across_all_four_observations": True,
        "view_rows": view_rows,
        "standard_view_comparisons": array_rows,
        "standard_view_max_absolute_difference_against_controls": max(
            item["maximum_absolute_difference_against_all_four_control_anchors"]
            for item in array_rows
        ),
        "standard_views_match_within_declared_absolute_tolerance": True,
        "initial_camera_parity_established": False,
        "initial_camera_scope": "candidate initial front orientations and shape-dependent camera transforms do not establish control camera parity; only selected active rotation versus view7 is checked",
        "edit_controls": edit_controls,
        "edit_cases": edit_rows,
        "all_live_edit_feature_names_preserved": True,
        "all_feature_type_orders_preserved": True,
        "all_full_feature_names_preserved_through_reopen": False,
        "metric_maxima": {
            "all_candidate_phases": maximum_errors(metrics_rows),
            "view_candidates": maximum_errors(
                [item for item in metrics_rows if item["phase"] == "view"]
            ),
            "baseline_edit_reopen": maximum_errors(
                [item for item in metrics_rows if item["phase"] != "view"]
            ),
        },
        "images": image_results,
        "owner_visual_inspection": image_manifest["owner_visual_inspection"],
        "bounded_three_polygon_geometry_depth_save_reopen_passed": True,
        "acceptance_limits": {
            "exact_input_files_only": sorted(sources),
            "depth_edit_factor_only": 1.25,
            "sketch_driving_edits_established": False,
            "full_feature_name_preservation_established": False,
            "initial_camera_parity_established": False,
            "broader_native_feature_families_or_assemblies_established": False,
            "production_adapter": "read-only",
            "full_cad_goal_complete": False,
        },
    }


def main():
    directory = Path(__file__).resolve().parent
    result = analyze(directory)
    (directory / "Analysis.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "controls_healthy": result["controls_healthy_in_both_batches"],
                "bounded_geometry_depth_save_reopen_passed": result[
                    "bounded_three_polygon_geometry_depth_save_reopen_passed"
                ],
                "standard_view_arrays": result["counts"]["standard_view_arrays"],
                "standard_view_max_absolute_difference": result[
                    "standard_view_max_absolute_difference_against_controls"
                ],
                "metric_maxima": {
                    key: {
                        "absolute": value["max_absolute"]["absolute_error"],
                        "relative": value["max_relative"]["relative_error"],
                    }
                    for key, value in result["metric_maxima"][
                        "all_candidate_phases"
                    ].items()
                },
                "live_names_preserved": result["all_live_edit_feature_names_preserved"],
                "reopen_full_names_preserved": result[
                    "all_full_feature_names_preserved_through_reopen"
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
