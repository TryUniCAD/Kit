from argparse import ArgumentParser
from hashlib import sha256
import json
import math
from pathlib import Path


RAW = "2a7c6fa9c30fdd66209c6fb0a703467c6e985b3c87bf04a31d8229fafcc88bf0"
PACKET = "ce4b4c7c434732775104758686cb83723dcdeb31965f43b4f1fd09a51e9b9e96"
READBACK = "e50c75cfeefb4c81432657a1e12a30824bc5d99279b4544de86299d8e83936d7"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
EXPECTED = ("Accent", "Bmp", "Pair", "Drivers", "WideDrivers")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(path, expected=None):
    if expected is not None and digest(path) != expected:
        raise ValueError("evidence custody differs: " + path.name)
    return json.loads(path.read_bytes())


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def identity(value):
    if value["sha256"] != ORACLE or not value["version_matches"]:
        raise ValueError("native process identity differs")
    return {key: value[key] for key in ("process_id", "process_creation_filetime", "file_version", "file_version_words", "sha256", "bytes", "pe_machine", "version_matches")}


def close(actual, wanted):
    if not math.isclose(actual, wanted, rel_tol=2e-7, abs_tol=1e-12):
        raise ValueError("sanitized numeric evidence differs from independent prediction")


def state(value, predicted, expected_name):
    tree = value["tree"]
    if len(tree) != 25 or any(row["error"] != 0 or row["warning"] or row["suppressed"] for row in tree):
        raise ValueError("native tree status differs")
    if value["body_count"] != 1 or value["complete_solid_count"] != 1 or value["native_body_type"] != 0 or value["whats_wrong"] != 0:
        raise ValueError("native solid state differs")
    if value["topology"] != {"faces": 6, "edges": 12, "vertices": 8} or value["native_body_name"] != expected_name:
        raise ValueError("native topology or body name differs")
    for key, wanted in (("volume", predicted["volume_m3"]), ("area", predicted["area_m2"]), ("mass", predicted["mass_kg"])):
        close(value["mass"][key], wanted)
    for actual, wanted in zip(value["mass"]["com"], predicted["centre_of_mass_m"], strict=True):
        close(actual, wanted)
    rows = value["sketch_geometry"]
    if len(rows) != 4 or any(row["kind"] != "line" or row["construction"] for row in rows):
        raise ValueError("native contour differs")
    if not value["dimension_driving"] or any(not row["driving"] for row in value["actual_drivers"]):
        raise ValueError("native driver state differs")
    keys = ("configuration", "sketch_parents", "boss_parents", "sketch_relation_count", "sketch_has_display_dimensions", "dimension_m", "dimension_driving", "whats_wrong", "body_count", "mass", "native_body_name", "native_body_type", "complete_solid_count", "topology", "actual_drivers")
    return {key: value[key] for key in keys} | {
        "tree_rows": len(tree), "tree_all_clean": True,
        "tree_sha256": sha256(json.dumps(tree, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "ordinary_closed_line_count": len(rows),
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    raw = load(root / "NativePacket01/Inspection/Result.json", RAW)
    packet = load(root / "NativePacket01/Trial.json", PACKET)
    reads = load(root / "NativeDerivativeRead01/Report.json", READBACK)
    if not raw["passed"] or not raw["controls_healthy"] or not raw["frozen_inputs_unchanged"] or raw["distinct_processes"] != 17 or raw["heldout_inputs_read"] != 0 or raw["public_writer_enabled"] or raw["original_source_qualification"]:
        raise ValueError("native trial boundary differs")
    if tuple(row["name"] for row in packet["cases"]) != EXPECTED or not reads["passed"] or len(reads["rows"]) != 5:
        raise ValueError("native or SDK case membership differs")
    phases = {}
    process_keys = set()
    checks = 0
    states = 0
    for name, phase in raw["phases"].items():
        ident = identity(phase["oracle_identity"])
        key = (ident["process_id"], ident["process_creation_filetime"])
        if key in process_keys or not phase["passed"]:
            raise ValueError("native phase did not use an independent healthy process")
        process_keys.add(key)
        record_path = root / "NativePacket01/Inspection" / name / "Record.json"
        record = load(record_path, phase["record_sha256"])
        base = {"passed": True, "oracle_identity": ident, "record_sha256": phase["record_sha256"]}
        if name.startswith("Control"):
            if not record["opened"] or not record["rebuilt"] or record["open_errors"] != 0 or record["open_warnings"] != 0 or record["whats_wrong"] != 0 or record["bodies"] != 1:
                raise ValueError("pristine control did not pass")
            if any(record[field] for field in ("session_diagnostics", "controller_diagnostics", "dialogs", "progress_windows")):
                raise ValueError("control cleanup failed")
            phases[name] = base | {key: record[key] for key in ("opened", "rebuilt", "open_errors", "open_warnings", "whats_wrong", "bodies", "mass")}
            continue
        case = next(row for row in packet["cases"] if name.startswith(row["name"]))
        prediction = case["prediction"]
        plain = name.endswith("Plain")
        label = prediction["intent"]["feature"] if plain else prediction["body_label"]
        if phase["open_errors"] != 0 or phase["open_warnings"] != 0 or not phase["immutable_bytes"]:
            raise ValueError("candidate open or source immutability failed")
        if any(phase[field] for field in ("controller_diagnostics", "dialogs", "progress_windows")) or record["first_failure"] is not None or record["cleanup_errors"]:
            raise ValueError("candidate cleanup failed")
        rows = {}
        for state_name, value in phase["states"].items():
            edited = state_name == "Edited" or name.endswith("Reopen")
            wanted = prediction["edit"]["expected"] if edited else prediction["expected_initial"]
            rows[state_name] = state(value, wanted, label)
            states += 1
        checks += phase["numeric_check_count"]
        phases[name] = base | {"states": rows, "open_errors": 0, "open_warnings": 0, "immutable_bytes": True, "numeric_check_count": phase["numeric_check_count"], "diagnostics_empty": True}
        if name.endswith("Named"):
            if phase["save_status"] != [True, 0, 0] or phase["edit_status"] != 0:
                raise ValueError("named save/edit status differs")
            saved = root / "NativePacket01/Inspection" / name / "Edited.SLDPRT"
            if digest(saved) != phase["derivative_sha256"] or saved.stat().st_size != phase["derivative_bytes"]:
                raise ValueError("native derivative custody differs")
            phases[name].update({key: phase[key] for key in ("save_status", "edit_status", "derivative_sha256", "derivative_bytes")})
    if len(process_keys) != 17 or checks != 868 or states != 35:
        raise ValueError("native evidence totals differ")
    audit_rows = []
    for row in reads["rows"]:
        if not row["passed"] or row["exit_code"] != 0 or row["file_access_attempts"] or row["research_imports"] or row["unexpected_sdk_module_origins"] or not row["source_immutable"]:
            raise ValueError("SDK derivative audit failed")
        if len(row["observations"]) != 5 or not all(item["passed"] for item in row["observations"]):
            raise ValueError("SDK derivative mode failed")
        audit_rows.append({key: row[key] for key in ("case", "source_sha256", "report_sha256", "exit_code", "passed", "source_immutable")} | {"modes_passed": [item["mode"] for item in row["observations"]], "additional_file_accesses": 0, "unexpected_sdk_module_origins": 0, "research_imports": 0})
    receipt = {
        "schema": "kit.sw2026.sdk-named-output-native-measurement.v1",
        "task_id": "B04-SW2026-NAMED-BODY-WRITE", "delivery_pr": 121,
        "native_trial_passed": True, "confidence": "confirmed_for_the_disclosed_ordinary_profile",
        "native_report_sha256": RAW, "trial_sha256": PACKET,
        "host_transport_summary_sha256": digest(root / "NativeTransport01/Result.json"),
        "source_manifest_sha256": packet["source_manifest_sha256"],
        "source_only_process_proof_sha256": packet["process_proof_sha256"],
        "native_tools_sha256": packet["tools_sha256"],
        "controls_healthy": True, "native_processes": 17, "candidate_processes": 15,
        "numeric_checks": checks, "measured_candidate_states": states,
        "candidate_open_errors": 0, "candidate_open_warnings": 0,
        "save_statuses": [[True, 0, 0] for unused in range(5)],
        "source_inputs_immutable": True, "heldout_inputs_read": 0,
        "original_source_qualification": False, "public_writer_registration_changed": False,
        "native_partition_generated": False, "writer_runtime_file_process_network_attempts": 0,
        "document_density_preference_kg_m3": 1000.0, "effective_unassigned_body_density_kg_m3": 1.0,
        "edit_scope": "depth_only_all_width_height_depth_drivers_observed",
        "publication_timing": {"source_and_protocol_hashes_frozen_before_run": True, "repository_commit_preceded_run": False, "basis": "root_operator_attestation_no_retroactive_pre_run_commit_claim"},
        "sdk_native_derivative_readback": {"passed": True, "fresh_processes": 5, "public_mode_comparisons": 25, "observer_sha256": reads["observer_sha256"], "report_sha256": READBACK, "additional_file_accesses": 0, "rows": audit_rows},
        "phases": phases,
        "remaining": ["independent_width_and_height_edit_qualification", "source_specific_corner_and_center_anchor_composition", "original_named_part_semantic_and_lifecycle_comparison", "public_writer_registration", "cache_free_unicode_public_read_admission"],
    }
    args.output.mkdir(exist_ok=False)
    target = put(args.output, "re/solidworks/measurements/2026/SdkNamedOutputNative01.json", receipt)
    print(json.dumps({"path": str(target), "sha256": digest(target), "numeric_checks": checks, "states": states, "native_processes": len(process_keys)}))


if __name__ == "__main__":
    main()
