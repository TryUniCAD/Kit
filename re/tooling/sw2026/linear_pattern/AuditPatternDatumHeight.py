from argparse import ArgumentParser
from math import dist, fsum, isfinite
from pathlib import Path
from subprocess import check_output
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))

from AuditPatternDatumPlacement import ANGLE_PLANE, geometry_fields, replay
from AuditPatternEnvelope import binding_snapshot, capture
from Core import ArchiveError
from PatternDatumHeightPacket import (
    BUILD, CASE_NAMES, CONTROL, LANE, ORACLE, SPEC, TRIAL, arm_spec, artifact_name,
    checked, digest, encode, require, verified_plan, verify,
)
from RunPatternDatumHeight import RESULT_SCHEMA


STAGES = ("preselection", "created", "rebuilt", "reopened")
MINIMUM_TRANSVERSE_CONTRAST = 0.001


def metadata_view(raw):
    report = json.loads(raw)
    required = {"IRefPlane": "BoundingBox", "IMathPoint": "ArrayData"}
    bindings = report["datum_bounds"]
    require(set(bindings) == set(required) and report["angle"]["native_processes_started"] == 0,
            "verified registered display property bindings are absent")
    for role, name in required.items():
        row = bindings[role]
        require(row["property"] == name and row["invoke"] == 2 and row["arguments"] == 0
                and row["return_vartype"] == 12 and type(row["dispid"]) is int
                and row["guid"] == report["angle"]["interfaces"][role]["guid"],
                "registered display property differs " + role)
    return bindings


def source_records(out, summary, manifest):
    processes = []
    controls = {}
    require(set(summary["controls"]) == {"before", "after"}, "expected both native bracket controls")
    for side in ("before", "after"):
        checked_control = summary["controls"][side]
        control = json.loads(checked(out / ("Control" + side.title() + ".json"), checked_control["record_sha256"]))
        identity = control["oracle_identity"]
        require(checked_control["passed"] and control["opened"] and control["rebuilt"] and not control["dialogs"]
                and control["open_errors"] == control["open_warnings"] == control["whats_wrong"] == 0
                and control["sha256"] == CONTROL and identity["file_version"] == BUILD and identity["sha256"] == ORACLE,
                "the datum-height source is missing its exact clean bracket")
        controls[side] = identity["process_creation_filetime"]
    rows = summary["phases"]
    require([[row["case"], row["phase"]] for row in rows] == manifest["sequence"], "incomplete independent native phases")
    records = {}
    for row in rows:
        case, phase = row["case"], row["phase"]
        record = json.loads(checked(out / case / phase / "Record.json", row["sha256"]))
        identity = record["oracle_identity"]
        require(row["passed"] and record["passed"] and record["source_immutable"]
                and identity["file_version"] == BUILD and identity["sha256"] == ORACLE and identity["pe_machine"] == "0x8664"
                and not record["application_pids_before"] and not record["application_pids_after"]
                and not record["dialogs"] and not record["first_failure"] and not record["controller_diagnostics"]
                and record["checks"] and all(check["passed"] for check in record["checks"]),
                "source phase did not finish with a clean exact-build lifetime")
        processes.append(identity["process_creation_filetime"])
        records[(case, phase)] = record
    order = [controls["before"], *processes, controls["after"]]
    require(order == sorted(set(order)) == summary["process_creation_filetimes"] and len(order) == 6,
            "both controls must bracket four distinct candidate processes")
    return records


def observations(author, reopen, shape):
    require(binding_snapshot(author, "authored") == binding_snapshot(reopen, "reopened"),
            "actual seed, plane, live parameter identity or tree changed on native reopen")
    shape_after = shape["arms"][0]["expected_final"]
    require(author["pre_pattern"]["expected"] == shape["expected_before_pattern"]
            and author["authored"]["expected"] == reopen["reopened"]["expected"] == shape_after,
            "native phase did not use the exact frozen independent geometry")
    before_records = author["datum_display_checkpoints"]
    after_records = reopen["datum_display_checkpoints"]
    require(set(before_records) == set(STAGES[:-1]) and set(after_records) == {"reopened"},
            "native datum display stage inventory differs")
    checkpoints = before_records | after_records
    seed = author["marked_pattern_inputs"]
    created = author["authored"]
    require(seed["counts"] == {"-1": 2, "1": 1, "4": 1}
            and seed["seed"]["hex"] == created["pattern"]["seeds"][0]["reference"]["hex"]
            and seed["direction"]["hex"] in {checkpoints["preselection"][key]["hex"] for key in
                                            ("feature_reference", "geometry_reference")},
            "actual marked inputs do not belong to the same seed and measured plane")
    for stage, row in checkpoints.items():
        current = reopen["reopened"] if stage == "reopened" else created
        datum = current["datum"]
        expected_point = [(a + b) / 2 for a, b in zip(*row["model_diagonal_m"], strict=True)]
        require(row["datum"] == shape["direction_datum"]["name"]
                and row["feature_reference"]["hex"] == datum["feature_reference"]["hex"]
                and row["geometry_reference"]["hex"] == datum["geometry_reference"]["hex"]
                and row["frame"]["origin_m"] == datum["origin_m"]
                and row["frame"]["normal"] == datum["normal"]
                and row["frame"]["transform"] == datum["transform"]
                and row["midpoint_m"] == expected_point and all(isfinite(x) for x in expected_point),
                "source display diagonal failed its exact named model-plane join: " + stage)
    return checkpoints


def inspect_case(out, case, plan, locked_artifact, records):
    author, reopen = (records[(case, name)] for name in ("author", "pristine-reopen"))
    save = author["save"]
    require(locked_artifact["name"] == artifact_name(case)
            and save["artifact"] == author["artifact"] == reopen["artifact"] == locked_artifact
            and save["ok"] and save["errors"] == save["warnings"] == 0
            and reopen["open"] == {"opened": True, "errors": 0, "warnings": 0},
            "native save and immutable readback do not own the same clean part")
    raw = checked(out / case / artifact_name(case), locked_artifact["sha256"], locked_artifact["bytes"])
    shape = arm_spec(plan, case)
    before_after = observations(author, reopen, shape)
    snapshot = reopen["reopened"]
    result = {"artifact": locked_artifact, "native_checks": len(author["checks"]) + len(reopen["checks"]),
              "native_geometry": {"before": author["pre_pattern"]["mass"], "after": snapshot["mass"],
                                  "bounds_after": snapshot["bounds"]["minmax"]},
              "datum_checkpoints": before_after}
    try:
        archive = capture(raw, snapshot, shape)
        model, roots, reciprocal = replay(raw)
    except (ArchiveError, KeyError, ValueError, TypeError, RuntimeError) as error:
        result["archive_refusal"] = {"type": type(error).__name__, "message": str(error)}
        return result
    result["archive"] = archive
    result["reciprocal_linked_replay"] = reciprocal
    try:
        display = geometry_fields(model, roots, ANGLE_PLANE)
        result["saved_display_formula"] = display
        stored_corners = display["rect_corners_model_m"]
        live_diagonal = before_after["reopened"]["model_diagonal_m"]
        result["native_diagonal_distance_to_saved_corners_m"] = [
            min(dist(point, saved) for saved in stored_corners) for point in live_diagonal
        ]
    except (KeyError, ValueError, TypeError, RuntimeError) as error:
        result["prior_display_formula_refusal"] = {"type": type(error).__name__, "message": str(error)}
    return result


def compare_arms(cases, spec):
    low, high = (cases[case] for case in CASE_NAMES)
    first = low["datum_checkpoints"]["preselection"]["frame"]
    require(all(row["frame"] == first for case in cases.values() for row in case["datum_checkpoints"].values()),
            "native height arms differ in selected plane frame")
    v = first["transform"][3:6]
    shifts = {}
    for stage in STAGES:
        from_centre, to_centre = (case["datum_checkpoints"][stage]["midpoint_m"] for case in (low, high))
        shifts[stage] = fsum((b - a) * basis for a, b, basis in zip(from_centre, to_centre, v, strict=True))
    if any("archive_refusal" in case for case in cases.values()):
        return {"disposition": "typed_source_unresolved", "observed_transverse_shift_by_stage_m": shifts}
    tol = spec["comparison_tolerance_m"]
    for observed, expected in zip((low, high), spec["arms"], strict=True):
        point = observed["archive"]["fc8_point_m"]
        observed["distances_m"] = {stage: dist(point, row["midpoint_m"])
                                    for stage, row in observed["datum_checkpoints"].items()}
        observed["distances_m"]["projected_stock"] = dist(point, expected["expected_stock_projection_m"])
        observed["distances_m"]["hinge_square_hypothesis"] = dist(point, expected["hypothesized_display_projection_m"])
    tested = [stage for stage in STAGES if abs(shifts[stage]) > MINIMUM_TRANSVERSE_CONTRAST]
    matches = [stage for stage in tested if all(case["distances_m"][stage] <= tol for case in cases.values())]
    stock_matches = all(case["distances_m"]["projected_stock"] <= tol for case in cases.values())
    if not tested:
        disposition = "insufficient_measured_transverse_contrast"
    elif matches and not stock_matches:
        disposition = "matches_measured_datum_display"
    elif stock_matches and not matches:
        disposition = "matches_projected_stock"
    else:
        disposition = "unresolved_display_or_stock_relation"
    return {"disposition": disposition, "minimum_transverse_contrast_m": MINIMUM_TRANSVERSE_CONTRAST,
            "comparison_tolerance_m": tol, "observed_transverse_shift_by_stage_m": shifts,
            "discriminating_stages": tested, "matching_display_stages": matches,
            "projected_stock_matches_both": stock_matches}


def audit(trial, pin, result_digest, output):
    require(trial.name == TRIAL, "audit only the new disclosed datum-height packet")
    packet = trial / "Packet"
    manifest = verify(packet, pin)
    revision = manifest["research_revision"]
    require(digest(HERE.read_bytes()) == manifest["host_audit_sha256"], "audit implementation differs from the packet")
    check_output(("git", "merge-base", "--is-ancestor", revision, "HEAD"), cwd=ROOT)
    require(not check_output(("git", "diff", "--name-only", revision, "--", "src", "re/tooling/sw2026/serial", LANE), cwd=ROOT),
            "host decoder or packet helpers changed relative to the frozen revision")
    out = trial / "DisclosedHeights"
    result = json.loads(checked(out / "Result.json", result_digest))
    require(result["schema"] == RESULT_SCHEMA and result["cohort"] == "disclosed"
            and result["native_lifecycle_passed"] and result["distinct_processes"] == 6 and result["packet_unchanged"]
            and result["artifacts_unchanged"] and result["native_build"] == BUILD and result["oracle_sha256"] == ORACLE
            and result["packet_sha256"] == pin and result["spec_sha256"] == SPEC and result["research_revision"] == revision
            and result["writer_output_count"] == result["heldout_sources_accessed"] == 0
            and result["application_pids_before"] == result["application_pids_after"] == []
            and set(result["artifacts"]) == set(CASE_NAMES), "unqualified native datum-height lifecycle")
    bindings = metadata_view(checked(out / "RegisteredApi.json", result["metadata_sha256"]))
    records = source_records(out, result, manifest)
    low, high = (records[(case, "pristine-reopen")]["reopened"] for case in CASE_NAMES)
    require(all(low[key] == high[key] for key in ("plate_profile", "seed_profile", "tree"))
            and low["pattern"]["values"] == high["pattern"]["values"]
            and low["datum"]["hinge"]["parents"] == high["datum"]["hinge"]["parents"]
            and low["pattern"]["parents"] == high["pattern"]["parents"],
            "actual source arms differ in XY profiles, tree, pattern parameters or named axis/seed roles")
    plan = verified_plan(packet / "Spec.json")
    cases = {case: inspect_case(out, case, plan, result["artifacts"][case], records) for case in CASE_NAMES}
    disposition = compare_arms(cases, plan)
    require(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com")
                    for name in sys.modules), "datum-height host audit imported CAD runtime")
    receipt = {"schema": "kit.sw2026.linear-pattern-datum-height-evidence.v1",
               "packet_sha256": pin, "native_result_sha256": result_digest, "spec_sha256": SPEC, "source_revision": revision,
               "registered_properties": bindings, "cases": cases, "discriminator": disposition,
               "native_processes_started_on_host": 0, "generated_parts": 0, "heldouts": 0}
    with output.open("xb") as stream:
        stream.write(encode(receipt))
    print(json.dumps({"receipt_sha256": digest(output.read_bytes()), "disposition": disposition["disposition"]}))
    return int(disposition["disposition"] == "typed_source_unresolved")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--trial", type=Path, required=True)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--result-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(audit(args.trial, args.packet_sha256, args.result_sha256, args.output))
