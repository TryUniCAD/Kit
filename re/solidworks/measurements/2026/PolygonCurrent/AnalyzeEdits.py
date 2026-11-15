from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from Analyze import comparison, load, metrics, neutral_metrics, numbers, sha256


def native_status(row):
    identity = row["oracle_identity"]
    numbers(
        [row["mass"][key] for key in ["volume", "area", "mass"]], 3, "mass properties"
    )
    numbers(row["mass"]["com"], 3, "center of mass")
    status = {
        "opened": row.get("opened") is True,
        "zero_load_errors": row.get("open_errors") == 0,
        "zero_load_warnings": row.get("open_warnings") == 0,
        "rebuilt": row.get("rebuilt") is True,
        "one_body": row.get("bodies") == 1,
        "zero_whats_wrong": row.get("whats_wrong") == 0,
        "features_clean_and_unsuppressed": bool(row.get("features"))
        and all(
            item.get("error") == 0
            and item.get("warning") is False
            and item.get("suppressed") is False
            and not item.get("error_query_error")
            and not item.get("suppression_query_error")
            for item in row["features"]
        ),
        "no_measurement_exception": not any(
            row.get(key)
            for key in [
                "exception",
                "measurement_exception",
                "failure_stage",
                "exception_stage",
            ]
        ),
        "no_controller_diagnostics": row.get("controller_diagnostics") == [],
        "no_dialogs_or_progress_windows": row.get("dialogs") == []
        and row.get("progress_windows") == [],
        "exact_oracle_identity": identity.get("version_matches") is True
        and identity.get("file_version") == "34.5.2.0604"
        and identity.get("sha256")
        == "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
        and identity.get("pe_machine") == "0x8664",
    }
    return status


def feature_tree(row):
    return [{"name": item["name"], "type": item["type"]} for item in row["features"]]


def depth_readback(row, parameter):
    feature_name = parameter.split("@")[1]
    values = [
        dimension["value"]
        for feature in row["features"]
        if feature["name"] == feature_name
        for dimension in feature.get("dims", [])
        if dimension["name"].split("@")[:2] == parameter.split("@")
    ]
    if len(values) != 1:
        raise ValueError("recorded extrusion-depth readback is absent or ambiguous")
    return values[0]


def analyze(directory):
    report = load(directory / "EditReport.json")
    provenance = load(directory / "Provenance.json")
    job = load(directory / "EditJob.json")
    baselines = {
        item["name"]: item for item in load(directory / "BaselineInputs.json")["cases"]
    }
    inputs = {
        item["name"].removesuffix(".SLDPRT"): item["sha256"]
        for item in provenance["generated_input_manifest"]
    }
    if [item["name"] for item in report["cases"]] != [
        item["name"] for item in job["cases"]
    ]:
        raise ValueError("recorded edit case order differs from the original job")
    if len(report["cases"]) != 3:
        raise ValueError("the controlled polygon edit batch requires three candidates")
    tolerances = {
        "relative_geometry": 1e-9,
        "m3": 1e-15,
        "m2": 1e-12,
        "m": 1e-12,
        "kg": 1e-15,
    }
    control_rows = [report["control_before"], report["control_after"]]
    controls = []
    all_rows = list(control_rows)
    for label, row in zip(["before", "after"], control_rows):
        status = native_status(row)
        status["recorded_control_hash_matches"] = (
            row["sha256"] == provenance["original_control_sha256"]
        )
        controls.append(
            {
                "phase": label,
                "status": status,
                "status_passed": all(status.values()),
                "mass_properties": row["mass"],
                "process_id": row["oracle_identity"]["process_id"],
                "process_creation_filetime": row["oracle_identity"][
                    "process_creation_filetime"
                ],
            }
        )
    cases = []
    for recorded, request in zip(report["cases"], job["cases"]):
        neutral = baselines[recorded["name"]]["neutral_input"]
        modified = copy.deepcopy(neutral)
        modified["depth_m"] = request["value_m"]
        expected = {
            "baseline": neutral_metrics(neutral),
            "edit": neutral_metrics(modified),
            "reopened": neutral_metrics(modified),
        }
        phases = {}
        for phase in ["baseline", "edit", "reopened"]:
            row = recorded[phase]
            all_rows.append(row)
            status = native_status(row)
            measured = row["mass"]
            depth = depth_readback(row, request["parameter"])
            target = neutral["depth_m"] if phase == "baseline" else request["value_m"]
            phase_result = {
                "native_status": status,
                "native_status_passed": all(status.values()),
                "process_id": row["oracle_identity"]["process_id"],
                "process_creation_filetime": row["oracle_identity"][
                    "process_creation_filetime"
                ],
                "body_count": row["bodies"],
                "feature_count": len(row["features"]),
                "measured_mass_properties": measured,
                "neutral_model_comparison": metrics(
                    measured, expected[phase], tolerances
                ),
                "job_expected_comparison": metrics(
                    measured,
                    request["expected"]["before" if phase == "baseline" else "after"],
                    tolerances,
                ),
                "depth_readback_m": comparison(depth, target, 1e-12, 0),
            }
            phases[phase] = phase_result
        edit = recorded["edit"]
        source_unchanged = (
            recorded.get("unchanged_source") is True
            and recorded["source_sha256_before"]
            == recorded["source_sha256_after"]
            == inputs[recorded["name"]]
        )
        saved_reopened_hash_matches = (
            edit["edited_copy_sha256"] == recorded["reopened"]["sha256"]
        )
        saved_cleanly = (
            edit.get("saved") is True
            and edit.get("save_errors") == 0
            and edit.get("save_warnings") == 0
        )
        parameter_matches_request = (
            edit["parameter"] == request["parameter"]
            and edit["requested_value_m"]
            == edit["readback_value_m"]
            == request["value_m"]
        )
        depth_factor = request["value_m"] / neutral["depth_m"]
        volume_factor = (
            recorded["edit"]["mass"]["volume"] / recorded["baseline"]["mass"]["volume"]
        )
        trees = {
            phase: feature_tree(recorded[phase])
            for phase in ["baseline", "edit", "reopened"]
        }
        tree_changes = {
            phase: [
                {"index": index, "baseline": before, "measured": after}
                for index, (before, after) in enumerate(
                    zip(trees["baseline"], trees[phase])
                )
                if before != after
            ]
            for phase in ["edit", "reopened"]
        }
        flags = {
            key: recorded.get(key) is True
            for key in ["baseline_match", "edit_match", "reopen_match"]
        }
        phases_passed = all(
            value["native_status_passed"]
            and value["neutral_model_comparison"]["within_tolerance"]
            and value["job_expected_comparison"]["within_tolerance"]
            and value["depth_readback_m"]["within_tolerance"]
            for value in phases.values()
        )
        cases.append(
            {
                "name": recorded["name"],
                "parameter": request["parameter"],
                "source_sha256": inputs[recorded["name"]],
                "edited_copy_sha256": edit["edited_copy_sha256"],
                "source_unchanged": source_unchanged,
                "edited_copy_digest_matches_fresh_reopen_input": saved_reopened_hash_matches,
                "saved_without_errors_or_warnings": saved_cleanly,
                "parameter_and_readback_match_requested_depth": parameter_matches_request,
                "depth_factor": depth_factor,
                "measured_volume_factor": volume_factor,
                "volume_factor_comparison": comparison(
                    volume_factor, depth_factor, 1e-12, 0
                ),
                "feature_name_and_type_order_preserved_through_edit_and_reopen": feature_tree(
                    recorded["baseline"]
                )
                == feature_tree(recorded["edit"])
                == feature_tree(recorded["reopened"]),
                "feature_type_order_preserved_through_edit_and_reopen": [
                    item["type"] for item in trees["baseline"]
                ]
                == [item["type"] for item in trees["edit"]]
                == [item["type"] for item in trees["reopened"]],
                "feature_tree_changes_from_baseline": tree_changes,
                "native_result_flags": flags,
                "phases": phases,
                "bounded_geometry_depth_edit_reopen_passed": source_unchanged
                and saved_reopened_hash_matches
                and saved_cleanly
                and parameter_matches_request
                and phases_passed
                and all(flags.values()),
            }
        )
    lifetimes = [
        (
            row["oracle_identity"]["process_id"],
            row["oracle_identity"]["process_creation_filetime"],
        )
        for row in all_rows
    ]
    controls_healthy = report.get("controls_healthy") is True and all(
        value["status_passed"] for value in controls
    )
    return {
        "schema": 1,
        "authority": "derived analysis of completed native depth edits and saved-copy reopening; no CAD execution",
        "source_revision": provenance["generator"]["source_head"],
        "original_native_report_sha256": provenance["original_sources"][
            "EditReport.json"
        ]["sha256"],
        "published_inputs_sha256": {
            name: sha256(directory / name)
            for name in [
                "EditReport.json",
                "EditJob.json",
                "Provenance.json",
                "BaselineInputs.json",
                "Analyze.py",
                "AnalyzeEdits.py",
            ]
        },
        "measurement_window_utc": {
            key: datetime.fromtimestamp(report[key], timezone.utc).isoformat()
            for key in ["started_at", "finished_at"]
        },
        "native_job_hash_matches_original": report["job_sha256"]
        == provenance["original_sources"]["EditJob.json"]["sha256"],
        "native_inspector_hash_matches_staged_tool": report["inspector_sha256"]
        == provenance["inspector"]["files"]["InspectEdit.py"]["sha256"],
        "counts": {
            "candidates": len(cases),
            "controls": len(controls),
            "native_process_lifetimes": len(lifetimes),
            "distinct_native_process_lifetimes": len(set(lifetimes)),
            "baseline_edit_reopen_snapshots": len(cases) * 3,
        },
        "fresh_process_lifetime_per_snapshot": len(lifetimes) == len(set(lifetimes)),
        "controls_healthy": controls_healthy,
        "control_mass_properties_identical": control_rows[0]["mass"]
        == control_rows[1]["mass"],
        "tolerances": tolerances,
        "controls": controls,
        "cases": cases,
        "native_geometry_edit_reopen_passed_flag": report.get(
            "geometry_edit_reopen_passed"
        )
        is True,
        "three_polygon_depth_edit_save_reopen_passed": controls_healthy
        and report.get("geometry_edit_reopen_passed") is True
        and all(value["bounded_geometry_depth_edit_reopen_passed"] for value in cases),
        "all_native_feature_names_and_type_orders_preserved_within_each_case": all(
            value["feature_name_and_type_order_preserved_through_edit_and_reopen"]
            for value in cases
        ),
        "all_native_feature_type_orders_preserved_within_each_case": all(
            value["feature_type_order_preserved_through_edit_and_reopen"]
            for value in cases
        ),
        "full_cad_acceptance_established": False,
        "acceptance_limits": [
            "three named polygon parts and one depth multiplication by 1.25 only",
            "native saved-copy reopening changes the material-folder label in all three cases; full feature-name preservation is not established",
            "no sketch driving-dimension edit",
            "no broader feature-family, assembly, source-conversion or production writer acceptance",
            "saved-copy fingerprints are recorded; native CAD file streams were not read during this publication",
        ],
    }


def main():
    directory = Path(__file__).resolve().parent
    result = analyze(directory)
    (directory / "EditAnalysis.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "controls_healthy": result["controls_healthy"],
                "bounded_depth_edit_save_reopen_passed": result[
                    "three_polygon_depth_edit_save_reopen_passed"
                ],
                "distinct_process_lifetimes": result["counts"][
                    "distinct_native_process_lifetimes"
                ],
                "full_feature_names_and_types_preserved": result[
                    "all_native_feature_names_and_type_orders_preserved_within_each_case"
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
