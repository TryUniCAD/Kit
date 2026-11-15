from __future__ import annotations

import hashlib
import json
import math
import struct
from datetime import datetime, timezone
from pathlib import Path


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numbers(values, size, label):
    if not isinstance(values, list) or len(values) != size:
        raise ValueError(f"{label} must contain exactly {size} numbers")
    if any(
        type(value) not in (int, float) or not math.isfinite(value) for value in values
    ):
        raise ValueError(f"{label} contains a nonfinite or nonnumeric value")
    return values


def maximum_delta(left, right):
    if len(left) != len(right):
        raise ValueError("comparison lengths differ")
    return max((abs(a - b) for a, b in zip(left, right)), default=0.0)


def comparison(actual, expected, absolute_tolerance, relative_tolerance):
    numbers([actual, expected], 2, "scalar comparison")
    difference = abs(actual - expected)
    tolerance = max(absolute_tolerance, abs(expected) * relative_tolerance)
    return {
        "measured": actual,
        "expected": expected,
        "absolute_difference": difference,
        "tolerance": tolerance,
        "within_tolerance": difference <= tolerance,
    }


def metrics(actual, expected, tolerances):
    result = {}
    for key, unit in [("volume", "m3"), ("area", "m2")]:
        result[key] = comparison(
            actual[key],
            expected[key],
            tolerances[unit],
            tolerances["relative_geometry"],
        )
    actual_com = numbers(actual["com"], 3, "measured center of mass")
    expected_com = numbers(expected["com"], 3, "expected center of mass")
    result["center_of_mass_m"] = [
        comparison(a, b, tolerances["m"], tolerances["relative_geometry"])
        for a, b in zip(actual_com, expected_com)
    ]
    result["within_tolerance"] = all(
        result[key]["within_tolerance"] for key in ["volume", "area"]
    )
    result["within_tolerance"] &= all(
        item["within_tolerance"] for item in result["center_of_mass_m"]
    )
    if "mass" in expected:
        result["mass_kg"] = comparison(
            actual["mass"],
            expected["mass"],
            tolerances["kg"],
            tolerances["relative_geometry"],
        )
        result["within_tolerance"] &= result["mass_kg"]["within_tolerance"]
    return result


def neutral_metrics(model):
    points = model["vertices_m"]
    if model["plane_axis"] != "z" or len(points) < 3:
        raise ValueError("this baseline derivation requires a z-plane polygon")
    for point in points:
        numbers(point, 2, "neutral polygon point")
    depth = model["depth_m"]
    density = model["density_kg_m3"]
    numbers([depth, density], 2, "neutral depth and density")
    if depth <= 0 or density <= 0:
        raise ValueError("neutral depth and density must be positive")
    pairs = list(zip(points, points[1:] + points[:1]))
    crosses = [a[0] * b[1] - b[0] * a[1] for a, b in pairs]
    twice_signed_area = math.fsum(crosses)
    if twice_signed_area == 0:
        raise ValueError("neutral polygon area is zero")
    area = abs(twice_signed_area) / 2
    perimeter = math.fsum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in pairs)
    center = [
        math.fsum((a[axis] + b[axis]) * cross for (a, b), cross in zip(pairs, crosses))
        / (3 * twice_signed_area)
        for axis in [0, 1]
    ]
    volume = area * depth
    return {
        "bodies": 1,
        "volume": volume,
        "area": 2 * area + perimeter * depth,
        "com": [*center, depth / 2],
        "mass": density * volume,
    }


def rotations(row):
    result = {}
    for phase in ["before", "after"]:
        value = row["rotations_" + phase]
        if set(value["standard"]) != {str(index) for index in range(1, 10)}:
            raise ValueError("standard-view IDs must be exactly 1 through 9")
        standard = {
            key: numbers(array, 9, row["name"] + " standard view " + key)
            for key, array in value["standard"].items()
        }
        active = numbers(value["active"], 16, row["name"] + " active transform")
        result[phase] = {"standard": standard, "active": active}
    return result


def image_evidence(directory, manifest, rows):
    result = []
    for image in manifest["images"]:
        row = rows[image["case"]]
        native_key = "initial_bitmap" if image["phase"] == "initial" else "bitmap"
        bmp = image["native_bmp"]
        png = image["published_png"]
        data = (directory / png["path"]).read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
            raise ValueError("published image is not a PNG with an IHDR")
        width, height = struct.unpack(">II", data[16:24])
        result.append(
            {
                "case": image["case"],
                "phase": image["phase"],
                "png": png["path"],
                "png_sha256": hashlib.sha256(data).hexdigest(),
                "png_matches_staged_digest": hashlib.sha256(data).hexdigest()
                == png["sha256"],
                "png_dimensions": [width, height],
                "png_metadata_matches_manifest": len(data) == png["bytes"]
                and [width, height] == [png["width"], png["height"]],
                "bmp_digest_matches_native_report": bmp["sha256"]
                == row[native_key + "_sha256"],
                "bmp_length_matches_native_report": bmp["bytes"]
                == row[native_key + "_bytes"],
                "bmp_original_retained_external_only": bmp["retained_external_only"],
            }
        )
    if (
        len(result) != 10
        or len({(item["case"], item["phase"]) for item in result}) != 10
    ):
        raise ValueError("this batch requires ten distinct case/phase images")
    return result


def analyze(directory):
    report = load(directory / "NativeViewReport.json")
    provenance = load(directory / "Provenance.json")
    baselines = load(directory / "BaselineInputs.json")
    image_manifest = load(directory / "ImageManifest.json")
    rows = report["results"]
    if [(row["name"], row["kind"]) for row in rows] != [
        (row["name"], row["kind"]) for row in provenance["case_order"]
    ]:
        raise ValueError("native rows differ from original ordered job")
    controls = [row for row in rows if row["kind"] == "control"]
    if (
        len(rows) != 5
        or len(controls) != 2
        or rows[0] is not controls[0]
        or rows[-1] is not controls[-1]
    ):
        raise ValueError("this batch requires controls around three candidates")
    expected_by_name = {row["name"]: row for row in baselines["cases"]}
    source_digests = {
        row["name"].removesuffix(".SLDPRT"): row["sha256"]
        for row in provenance["generated_input_manifest"]
    }
    source_digests.update(
        {row["name"]: provenance["original_control_sha256"] for row in controls}
    )
    view_data = {row["name"]: rotations(row) for row in rows}
    tolerances = {
        "rotation_coefficient_absolute": 1e-12,
        "relative_geometry": 1e-9,
        "m3": 1e-15,
        "m2": 1e-12,
        "m": 1e-12,
        "kg": 1e-15,
        "depth_m_absolute": 1e-12,
        "formula": "absolute difference <= max(absolute tolerance, relative tolerance * abs(expected)); rotation and depth use only absolute tolerance",
    }
    control_views = [
        view_data[row["name"]][phase]["standard"]
        for row in controls
        for phase in ["before", "after"]
    ]
    case_results = []
    for row in rows:
        identity = row["oracle_identity"]
        views = view_data[row["name"]]
        status = {
            "opened": row.get("opened") is True,
            "zero_open_errors": row.get("open_errors") == 0,
            "zero_open_warnings": row.get("open_warnings") == 0,
            "rebuilt": row.get("rebuilt") is True,
            "one_body": row.get("bodies") == 1,
            "features_clean_and_unsuppressed": bool(row.get("features"))
            and all(
                feature.get("error") == 0
                and feature.get("warning") is False
                and feature.get("suppressed") is False
                for feature in row["features"]
            ),
            "no_recorded_exception_or_cleanup_error": not any(
                row.get(key)
                for key in [
                    "exception",
                    "failure_stage",
                    "cleanup_error",
                    "cleanup_errors",
                ]
            ),
            "no_controller_diagnostics": row.get("controller_diagnostics") == [],
            "no_dialogs_or_progress_windows": row.get("dialogs") == []
            and row.get("progress_windows") == [],
            "initial_and_selected_bitmaps_saved": row.get("initial_bitmap_saved")
            is True
            and row.get("bitmap_saved") is True,
            "input_digest_unchanged": row.get("unchanged_input") is True
            and row["sha256"] == row["sha256_after"],
            "input_digest_matches_staged_manifest": row["sha256"]
            == source_digests[row["name"]],
            "exact_oracle_identity": identity["version_matches"] is True
            and identity["file_version"] == "34.5.2.0604"
            and identity["sha256"]
            == "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe",
            "completed_capture_stage": row["stage"] == "capture_return",
        }
        per_phase = {}
        for phase in ["before", "after"]:
            per_view = {
                key: max(
                    maximum_delta(value, control[key]) for control in control_views
                )
                for key, value in views[phase]["standard"].items()
            }
            discrepancy = max(per_view.values())
            per_phase[phase] = {
                "comparison": "each view against the same view from both controls, before and after selection",
                "per_view_max_absolute_difference": per_view,
                "maximum_absolute_difference": discrepancy,
                "within_tolerance": discrepancy
                <= tolerances["rotation_coefficient_absolute"],
            }
        after_delta = maximum_delta(
            views["after"]["active"][:9], views["after"]["standard"]["7"]
        )
        numbers(
            [row["mass"]["volume"], row["mass"]["area"], row["mass"]["mass"]],
            3,
            "mass-property scalars",
        )
        numbers(row["mass"]["com"], 3, "mass-property center")
        result = {
            "name": row["name"],
            "kind": row["kind"],
            "process_id": identity["process_id"],
            "process_creation_filetime": identity["process_creation_filetime"],
            "source_sha256": row["sha256"],
            "native_status": status,
            "native_status_passed": all(status.values()),
            "feature_count": len(row["features"]),
            "bodies": row["bodies"],
            "measured_mass_properties": row["mass"],
            "canonical_view_parity": per_phase,
            "standard_views_unchanged_by_selection_max_absolute_difference": max(
                maximum_delta(value, views["after"]["standard"][key])
                for key, value in views["before"]["standard"].items()
            ),
            "after_active_rotation_vs_own_isometric": {
                "maximum_absolute_difference": after_delta,
                "within_tolerance": after_delta
                <= tolerances["rotation_coefficient_absolute"],
            },
            "initial_active_rotation_vs_controls_max_absolute_difference": max(
                maximum_delta(
                    views["before"]["active"][:9],
                    view_data[control["name"]]["before"]["active"][:9],
                )
                for control in controls
            ),
            "initial_active_rotation_vs_identity_max_absolute_difference": maximum_delta(
                views["before"]["active"][:9], [1, 0, 0, 0, 1, 0, 0, 0, 1]
            ),
        }
        if row["name"] in expected_by_name:
            baseline = expected_by_name[row["name"]]
            result["baseline_comparison"] = metrics(
                row["mass"], baseline["expected_baseline"], tolerances
            )
            result["neutral_model_comparison"] = metrics(
                row["mass"], neutral_metrics(baseline["neutral_input"]), tolerances
            )
            dimensions = [
                dimension["value"]
                for feature in row["features"]
                if feature["name"] == baseline["neutral_input"]["extrusion_name"]
                for dimension in feature.get("dims", [])
                if dimension["name"].split("@")[0:2]
                == ["D1", baseline["neutral_input"]["extrusion_name"]]
            ]
            if len(dimensions) != 1:
                raise ValueError(
                    "candidate extrusion-depth readback is missing or ambiguous"
                )
            result["extrusion_depth_readback_m"] = comparison(
                dimensions[0],
                baseline["neutral_input"]["depth_m"],
                tolerances["depth_m_absolute"],
                0,
            )
        case_results.append(result)
    images = image_evidence(
        directory, image_manifest, {row["name"]: row for row in rows}
    )
    pids = [row["oracle_identity"]["process_id"] for row in rows]
    candidates = [row for row in case_results if row["kind"] == "generated-heldout"]
    return {
        "schema": 1,
        "authority": "derived analysis of already completed native report; no CAD execution",
        "source_revision": provenance["generator"]["source_head"],
        "synthetic_revision": provenance["generator"]["synthetic_commit"],
        "original_native_report_sha256": provenance["original_sources"][
            "NativeViewReport.json"
        ]["sha256"],
        "published_input_sha256": {
            name: sha256(directory / name)
            for name in [
                "NativeViewReport.json",
                "Provenance.json",
                "BaselineInputs.json",
                "ImageManifest.json",
                "Analyze.py",
            ]
        },
        "measurement_window_utc": {
            key: datetime.fromtimestamp(report[key], timezone.utc).isoformat()
            for key in ["started_at", "finished_at"]
        },
        "tolerances": tolerances,
        "counts": {
            "rows": len(rows),
            "controls": len(controls),
            "generated_candidates": len(candidates),
            "distinct_process_ids": len(set(pids)),
            "numeric_standard_rotation_arrays": len(rows) * 2 * 9,
            "numeric_active_transform_arrays": len(rows) * 2,
            "published_pngs": len(images),
        },
        "all_rotation_arrays_finite_numeric_with_required_lengths": True,
        "fresh_process_identity_distinct_per_row": len(set(pids)) == len(pids),
        "native_job_digest_matches_original_job": report["job_sha256"]
        == provenance["original_sources"]["ViewJob.json"]["sha256"],
        "native_inspector_digest_matches_staged_inspector": report["inspector_sha256"]
        == provenance["inspector"]["files"]["InspectView.py"]["sha256"],
        "control_mass_properties_identical": controls[0]["mass"] == controls[1]["mass"],
        "all_rows_clean_with_one_body_and_unchanged_input": all(
            row["native_status_passed"] for row in case_results
        ),
        "all_canonical_views_within_absolute_tolerance": all(
            row["canonical_view_parity"][phase]["within_tolerance"]
            for row in case_results
            for phase in ["before", "after"]
        ),
        "all_post_selection_active_rotations_match_own_isometric": all(
            row["after_active_rotation_vs_own_isometric"]["within_tolerance"]
            for row in case_results
        ),
        "maximum_standard_view_absolute_difference_against_controls": max(
            row["canonical_view_parity"][phase]["maximum_absolute_difference"]
            for row in case_results
            for phase in ["before", "after"]
        ),
        "candidate_baselines_and_neutral_geometry_within_tolerance": all(
            row["baseline_comparison"]["within_tolerance"]
            and row["neutral_model_comparison"]["within_tolerance"]
            and row["extrusion_depth_readback_m"]["within_tolerance"]
            for row in candidates
        ),
        "cases": case_results,
        "images": images,
        "all_published_images_match_recorded_bindings": all(
            all(
                image[key]
                for key in [
                    "png_matches_staged_digest",
                    "png_metadata_matches_manifest",
                    "bmp_digest_matches_native_report",
                    "bmp_length_matches_native_report",
                ]
            )
            for image in images
        ),
        "visual_inspection": provenance["visual_inspection"],
        "acceptance_boundaries": provenance["boundaries"],
        "byte_equivalent_artifact": load(directory / "ArtifactIdentity.json"),
        "not_established": [
            "initial active-camera parity with controls",
            "other source revisions beyond three independently verified byte-identical artifacts",
            "dimension edits or save/reopen in this viewport batch",
            "full CAD goal completion",
            "production SOLIDWORKS writing",
            "curve or assembly writer acceptance",
            "matrix byte identity or writer constants from captured rotations",
            "independent decoded-pixel equality between BMP and PNG",
        ],
    }


def main():
    directory = Path(__file__).resolve().parent
    result = analyze(directory)
    (directory / "Analysis.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "rows": result["counts"]["rows"],
                "standard_view_maximum_absolute_difference": result[
                    "maximum_standard_view_absolute_difference_against_controls"
                ],
                "source_revision": result["source_revision"],
            }
        )
    )


if __name__ == "__main__":
    main()
