from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from Analyze import comparison, load, metrics, neutral_metrics, numbers, sha256


def analyze(directory):
    report = load(directory / "FreshGeometryReport.json")
    provenance = load(directory / "Provenance.json")
    baseline = next(
        item
        for item in load(directory / "BaselineInputs.json")["cases"]
        if item["name"] == "H7_irregular"
    )
    rows = report["results"]
    if [item["kind"] for item in rows] != [
        "control_before",
        "candidate",
        "control_after",
    ]:
        raise ValueError(
            "fresh geometry requires exactly one candidate between controls"
        )
    tolerances = {
        "relative_geometry": 1e-9,
        "m3": 1e-15,
        "m2": 1e-12,
        "m": 1e-12,
        "kg": 1e-15,
    }
    expected_hash = next(
        item["sha256"]
        for item in provenance["generated_input_manifest"]
        if item["name"] == "H7_irregular.SLDPRT"
    )
    values = []
    for row in rows:
        identity = row["oracle_identity"]
        numbers(
            [row["mass"][key] for key in ["volume", "area", "mass"]],
            3,
            "mass properties",
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
            "native_healthy_flag": row.get("geometry_and_rebuild_healthy") is True,
            "exact_oracle_identity": identity.get("version_matches") is True
            and identity.get("file_version") == "34.5.2.0604"
            and identity.get("sha256")
            == "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
            and identity.get("pe_machine") == "0x8664",
            "recorded_input_hash_matches": row["sha256"]
            == (
                expected_hash
                if row["kind"] == "candidate"
                else provenance["original_control_sha256"]
            ),
            "completed_close_stage": row.get("stage") == "close_return",
        }
        values.append(
            {
                "kind": row["kind"],
                "process_id": identity["process_id"],
                "process_creation_filetime": identity["process_creation_filetime"],
                "source_sha256": row["sha256"],
                "status": status,
                "status_passed": all(status.values()),
                "feature_count": len(row["features"]),
                "body_count": row["bodies"],
                "mass_properties": row["mass"],
            }
        )
    candidate = rows[1]
    readback = [
        dimension["value"]
        for feature in candidate["features"]
        if feature["name"] == baseline["neutral_input"]["extrusion_name"]
        for dimension in feature.get("dims", [])
        if dimension["name"].split("@")[:2]
        == ["D1", baseline["neutral_input"]["extrusion_name"]]
    ]
    if len(readback) != 1:
        raise ValueError("heptagon depth readback is missing or ambiguous")
    baseline_comparison = metrics(
        candidate["mass"], baseline["expected_baseline"], tolerances
    )
    neutral_comparison = metrics(
        candidate["mass"], neutral_metrics(baseline["neutral_input"]), tolerances
    )
    depth_comparison = comparison(
        readback[0], baseline["neutral_input"]["depth_m"], 1e-12, 0
    )
    lifetimes = [
        (row["process_id"], row["process_creation_filetime"]) for row in values
    ]
    return {
        "schema": 1,
        "authority": "derived analysis of an already completed controlled native geometry inspection; no CAD execution",
        "source_revision": provenance["generator"]["source_head"],
        "original_native_report_sha256": provenance["original_sources"][
            "FreshGeometryReport.json"
        ]["sha256"],
        "published_inputs_sha256": {
            name: sha256(directory / name)
            for name in [
                "FreshGeometryReport.json",
                "FreshGeometryJob.json",
                "Provenance.json",
                "BaselineInputs.json",
                "Analyze.py",
                "AnalyzeGeometry.py",
            ]
        },
        "measurement_window_utc": {
            key: datetime.fromtimestamp(report[key], timezone.utc).isoformat()
            for key in ["started_at", "finished_at"]
        },
        "native_job_hash_matches_original": report["job_sha256"]
        == provenance["original_sources"]["FreshGeometryJob.json"]["sha256"],
        "native_inspector_hash_matches_staged_tool": report["inspector_sha256"]
        == provenance["inspector"]["files"]["InspectFresh.py"]["sha256"],
        "distinct_process_lifetime_per_row": len(set(lifetimes)) == 3,
        "controls_healthy": report["controls_healthy"] is True
        and all(value["status_passed"] for value in [values[0], values[2]]),
        "control_mass_properties_identical": rows[0]["mass"] == rows[2]["mass"],
        "all_rows_clean_with_one_body": all(value["status_passed"] for value in values),
        "tolerances": tolerances,
        "heptagon_baseline_comparison": baseline_comparison,
        "heptagon_neutral_geometry_comparison": neutral_comparison,
        "heptagon_depth_readback_m": depth_comparison,
        "candidate_geometry_within_tolerance": baseline_comparison["within_tolerance"]
        and neutral_comparison["within_tolerance"]
        and depth_comparison["within_tolerance"],
        "rows": values,
        "earlier_interruption": provenance["earlier_interruption"],
        "acceptance_limits": [
            "one heptagon geometry/rebuild repeat only",
            "no driving edit, save or saved-copy reopen in this batch",
            "input digest recorded before inspection; this report does not itself perform an after-inspection digest comparison",
            "no full feature-family or production writer acceptance",
        ],
    }


def main():
    directory = Path(__file__).resolve().parent
    result = analyze(directory)
    (directory / "GeometryAnalysis.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "controls_healthy": result["controls_healthy"],
                "all_rows_clean": result["all_rows_clean_with_one_body"],
                "geometry_matches": result["candidate_geometry_within_tolerance"],
            }
        )
    )


if __name__ == "__main__":
    main()
