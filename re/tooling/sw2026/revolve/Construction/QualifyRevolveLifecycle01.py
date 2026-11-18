from argparse import ArgumentParser
from hashlib import sha256
import json
from math import isclose
from pathlib import Path, PureWindowsPath


def digest(payload):
    return sha256(payload).hexdigest()


def checked(root, relative, expected=None, size=None):
    candidate = Path(relative)
    assert not candidate.is_absolute() and ".." not in candidate.parts
    path = root / candidate
    assert not path.is_symlink() and path.resolve(strict=True).is_relative_to(root)
    data = path.read_bytes()
    if expected is not None:
        assert digest(data) == expected, path.name
    if size is not None:
        assert len(data) == size, path.name
    return data


def states(phase, labels):
    assert phase["first_failure"] is None and not phase["cleanup_errors"] and not phase["controller_diagnostics"]
    assert phase["source_immutable"] and phase["inspection_completed"] and phase["passed"]
    assert phase["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
    assert phase["before_explicit_rebuild"]["needs_rebuild"] == phase["before_explicit_rebuild"]["whats_wrong"] == 0
    assert phase["checks"] and all(check["passed"] for check in phase["checks"])
    results = []
    for label in labels:
        row = phase[label]
        tree = row["complete_tree"]
        assert len(tree) == 25 and all(not value["error"] and not value["warning"] and not value["suppressed"] for value in tree)
        assert row["bodies"] == 1 and row["sketch_relation_count"] == 4 and not row["sketch_has_display_dimensions"]
        actual, expected = row["mass"], row["expected"]
        assert all(isclose(actual[key], expected[key], rel_tol=1e-6) for key in ("volume", "area"))
        assert all(isclose(value, wanted, rel_tol=1e-6, abs_tol=1e-12) for value, wanted in zip(actual["com"], expected["com"], strict=True))
        results.append({"state": label, "feature_rows": len(tree), "bodies": row["bodies"],
                        "sketch_relations": row["sketch_relation_count"], "angle_radians": row["angle_radians"],
                        "reversed": row["reverse"], "signed_sweep_handedness": row["forward_handedness"],
                        "actual": {"volume_m3": actual["volume"], "area_m2": actual["area"], "centre_m": actual["com"]},
                        "independent_prediction": {"volume_m3": expected["volume"], "area_m2": expected["area"], "centre_m": expected["com"]}})
    return results


def evidence(root, entry, opened, reopened):
    name = entry["model"]["name"]
    assert opened["job"]["case"] == entry["model"] and reopened["job"]["case"]["name"] == name
    source = checked(root, f"Inputs/{name}.SLDPRT", entry["sha256"])
    saved = checked(root, f"Inspection/Edited/{name}.SLDPRT", opened["edited_derivative"]["sha256"],
                    opened["edited_derivative"]["bytes"])
    assert digest(source) == opened["source_sha256"] and digest(saved) == reopened["source_sha256"]
    assert opened["edited_derivative"]["save_status"] == [True, 0, 0]
    assert opened["direction_matches_signed_target"] and reopened["direction_matches_signed_target"] and reopened["matches_edited_tree"]
    assert opened["display_dimension_preference"]["restored"] and opened["edit"]["passed"] and opened["edit"]["setter_status"] == 0
    for suffix, phase in (("reopen", opened), ("edited-reopen", reopened)):
        checked(root, f"Inspection/{name}.{suffix}.json", phase["phase_sha256"])
    return {"case": name, "input_sha256": digest(source), "saved_sha256": digest(saved),
            "numeric_checks": len(opened["checks"]) + len(reopened["checks"]),
            "raw_phase_sha256": [opened["phase_sha256"], reopened["phase_sha256"]],
            "live_driver": opened["edit"]["name"], "clean_save_status": opened["edited_derivative"]["save_status"],
            "candidate_states": states(opened, ("reopened", "edited")), "fresh_saved_states": states(reopened, ("reopened",))}


def processes(payload, names):
    return sorted(row["ProcessId"] for row in json.loads(payload) if row["Name"].lower() in names)


def host_evidence(root, transport_digest, immediate_pid):
    transport = checked(root, "RootNativeTransport01/Run01.json", transport_digest)
    state = json.loads(transport)
    assert state["status"] == "host_deadline" and state["deadline_kinds"] == ["no_progress"]
    assert state["transport_exit_confirmed"] and not state["automatic_guest_kill"] and not state["automatic_vm_reset"]
    assert not state["progress"]["history"]
    before = checked(root, "RootNativeTransport01/Before.1.stdout.json")
    interim = checked(root, "RootNativeTransport01/After.1.stdout.json")
    idle = checked(root, "RootNativeTransport01/AfterRecovery01.json")
    names = {"lmgrd.exe", "sw_d.exe"}
    license_pids = processes(before, names)
    assert license_pids == processes(interim, names) == processes(idle, names) == [4256, 4644, 4988]
    assert processes(before, {"sldworks.exe"}) == processes(idle, {"sldworks.exe"}) == []
    assert processes(interim, {"sldworks.exe"}) == [immediate_pid]
    return {"transport_sha256": digest(transport), "transport_status": state["status"],
            "transport_returncode": state["transport_returncode"], "progress_basename_used": "Record.json",
            "native_aggregate_basename": "Inspection.json", "initial_inventory_sha256": digest(before),
            "intermediate_inventory_sha256": digest(interim), "idle_inventory_sha256": digest(idle),
            "license_pids": license_pids, "one_interim_cad_pid": immediate_pid,
            "guest_kill": False, "vm_reset": False, "recovery_confirmed_idle": True}


def main():
    parser = ArgumentParser(description="Bind the ordinary revolve lifecycle to its exact native artifacts and host recovery")
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--native-sha256", required=True)
    parser.add_argument("--transport-sha256", required=True)
    args = parser.parse_args()
    root = args.packet.parent.resolve(strict=True)
    packet = json.loads(checked(root, args.packet.name, args.packet_sha256))
    job_bytes = checked(root, packet["job_path"])
    job = json.loads(job_bytes)
    assert len(packet["files"]) == 40 and packet["expected_fresh_processes"] == 10 and packet["heldout_inputs_read"] == 0
    for row in packet["files"]:
        checked(root, row["path"], row["sha256"], row["bytes"])
    native = json.loads(checked(root, "Inspection/Inspection.json", args.native_sha256))
    oracle_sha = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
    assert native["job_sha256"] == digest(job_bytes) and native["oracle_sha256"] == oracle_sha
    assert native["passed"] and native["controls_healthy"] and native["saved_edit_reopened"]
    assert native["distinct_processes"] == 10 and not native["heldout_acceptance"]
    assert len(native["cases"]) == len(native["derivative_reopens"]) == len(job["cases"]) == 4
    cases = [evidence(root, entry, opened, reopened) for entry, opened, reopened
             in zip(job["cases"], native["cases"], native["derivative_reopens"], strict=True)]
    control = checked(root, "Control/" + PureWindowsPath(job["control"]).name, job["control_sha256"])
    controls = []
    for phase, sample in zip(("control_before", "control_after"), native["controls"], strict=True):
        assert sample["kind"] == phase and sample["healthy"] and sample["sha256"] == digest(control)
        assert sample["open_errors"] == sample["open_warnings"] == sample["whats_wrong"] == 0 and sample["bodies"] == 1
        controls.append({"phase": phase, "healthy": True, "file_sha256": digest(control), "com_revision": sample["revision"]})
    identities = [value["oracle_identity"] for key in ("controls", "cases", "derivative_reopens") for value in native[key]]
    assert len(identities) == len({row["process_creation_filetime"] for row in identities}) == 10
    assert all(row["version_matches"] and row["file_version"] == "34.5.2.0604" and row["sha256"] == oracle_sha for row in identities)
    order = sorted(identities, key=lambda row: row["process_creation_filetime"])
    assert order[0] == native["controls"][0]["oracle_identity"] and order[-1] == native["controls"][1]["oracle_identity"]
    host = host_evidence(root, args.transport_sha256, native["cases"][-1]["oracle_identity"]["process_id"])
    receipt = {"schema": "kit.sw2026.disclosed-generated-revolve-native.v1", "packet_sha256": args.packet_sha256,
               "native_receipt_sha256": args.native_sha256, "constructor_source_manifest_sha256": packet["generator_source_manifest_sha256"],
               "frozen_input_files_reverified": len(packet["files"]), "native_lifecycle_passed": True,
               "heldout_acceptance": False, "public_writer_qualified": False, "saved_typed_join_pending": True,
               "hidden_inputs_read": 0, "oracle": {"version": "34.5.2.0604", "executable_sha256": oracle_sha},
               "distinct_native_processes": len(identities), "candidate_numeric_checks": sum(row["numeric_checks"] for row in cases),
               "processes": [{"pid": row["process_id"], "birth_filetime": row["process_creation_filetime"]} for row in order],
               "controls": controls, "cases": cases, "host": host}
    raw = (json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as file:
        file.write(raw)
    print(json.dumps({"native_lifecycle_passed": True, "controls_healthy": True, "native_processes": len(order),
                      "candidate_numeric_checks": receipt["candidate_numeric_checks"], "receipt_sha256": digest(raw)}))


if __name__ == "__main__":
    main()
