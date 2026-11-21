from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from math import isclose
from pathlib import Path, PureWindowsPath
import json

from AuditLiveReferenceCapture import KINDS, PHASES
from ReferencePacket import (BASELINE_M, CASES, DRIVERS, EDIT_HEIGHT_M, ORACLE, PREVIOUS_CAPTURE, PRIOR, PRIOR_WINDOWS, RECEIPTS,
                             SCHEMA, checked, read, require, verify_oracle)


RESULT = "3bc37b57f04e8424ed1362fd8584d56a7a0dfd6459962ea9859755f1530fd291"
PROBE = "05f1e6da9ade4004206eabb7ac6aa94726048b2c0573c94de73df0e0e3d45df3"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
LINEAGE = "SdkFreecadF14aTopologyLineage01.json"
GEOMETRY_STATES = {"edit_save": ("Initial", "Baseline", "Edited", "Saved"), "fresh_reopen": ("FreshOpen", "FreshRebuild")}
TRANSPORT = {"python_type": "memoryview", "dimensions": 1, "item_size": 1, "format": "B", "c_contiguous": True}


def reference(row, kind, status, equality):
    require(row["passed"] and not row.get("error") and row["resolver_status"] == status and row["resolver_returned_object"] and
            row["persistent_id_equality"] == row["resolved_object_equality"] == equality,
            "an actual native reference did not resolve to the same object")
    if kind in KINDS:
        require(row["selected_type"] == KINDS[kind][2] and row["selected_object_equality"] == equality,
                "native selection has another kind or actual object")
    count = row["reference"]["bytes"]
    require(row["reference_transport"] == TRANSPORT | {"bytes": count} and 0 < count <= 4096,
            "the native transport is outside the supported byte-array shape")
    return row["reference"]["sha256"], count


def controls(root, result, identities, status, equality):
    observations = {}
    for key, name in (("control_before", "ControlBefore"), ("control_after", "ControlAfter")):
        row = result[key]
        record = read(root, Path(name) / "Record.json", row["record_sha256"])
        transport = read(root, Path(name) / "ReferenceRecord.json", row["reference_record_sha256"])
        measured = record["measurement"]
        require(record == {key: value for key, value in row.items() if not key.endswith("record_sha256")}
                and record["passed"] and record["geometry_passed"] and record["reference_transport"]["passed"]
                and transport["job"] == {"role": name, "input_sha256": CONTROL} and transport["passed"]
                and transport["result"] == record["reference_transport"] and not transport["first_failure"]
                and not transport["cleanup_errors"] and measured["immutable_input"] and measured["opened"] and measured["rebuilt"]
                and measured["open_errors"] == measured["open_warnings"] == measured["whats_wrong"] == 0
                and not measured["controller_diagnostics"] and not measured["dialogs"] and measured["bodies"] == 1,
                "the exact native transport control or its clean one-body result changed")
        producer, = [feature for feature in measured["features"] if feature["name"] == "Boss-Extrude1"]
        require(producer["type"] == "Extrusion", "another actual feature owns the independent control body")
        identities.add(verify_oracle(row["oracle_identity"]))
        roles = transport["result"]["roles"]
        require(set(roles) == set(KINDS) | {"producer"}, "the native control did not calibrate all observed entity classes")
        sizes = {kind: reference(value, kind, status, equality)[1] for kind, value in roles.items()}
        observations[name] = {"record_sha256": row["record_sha256"], "reference_record_sha256": row["reference_record_sha256"],
                              "input_sha256": CONTROL, "producer": producer["name"], "self_resolved_token_bytes": sizes}
    return observations


def original_roles(lineage):
    rows = {(row["kind"], row["role"]): row for row in lineage["entity_rows"]}
    require(len(rows) == len(lineage["entity_rows"]) == 26, "the source Body and primitive role join is ambiguous")
    for kind, label in (("face", "Face"), ("edge", "Edge"), ("vertex", "Vertex")):
        entries = [row for key, row in rows.items() if key[0] == kind]
        ordinals = sorted(row["source_body"]["ordinal"] for row in entries)
        require(ordinals == list(range(1, lineage["portable_entity_counts"][kind] + 1)) and
                all(row["source_body"]["indexed_name"] == row["source_primitive"]["indexed_name"] ==
                    label + str(row["source_body"]["ordinal"]) and
                    row["source_body"]["ordinal"] == row["source_primitive"]["ordinal"] for row in entries),
                "the offline source ordinal and producer relationship changed")
    return rows


def geometry(state, wanted):
    require(state["configuration"] == "Default" and state["body_name"] == "Body" and state["body_count"] == 1 and
            state["body_topology"] == [8, 12, 6] and tuple(state["dimensions"]) == DRIVERS,
            "the measured reference state has another model or driver set")
    require(not any(row["suppressed"] or row["error"] or row["warning"] for row in state["tree"]),
            "the live native feature tree has unresolved diagnostics")
    for driver, value in zip(DRIVERS, wanted, strict=True):
        measured = state["dimensions"][driver]
        require(measured["short_name"] == driver and measured["driving"] and
                isclose(measured["value_m"], value, rel_tol=2e-7, abs_tol=1e-12), "an actual driving parameter changed owner or value")
    x, y, z = wanted
    mass = state["mass"]
    require(isclose(mass["volume"], x * y * z, rel_tol=2e-7) and
            isclose(mass["mass"], mass["volume"], rel_tol=2e-7) and
            isclose(mass["area"], 2 * (x * y + x * z + y * z), rel_tol=2e-7) and
            all(isclose(value, extent / 2, rel_tol=2e-7) for value, extent in zip(mass["com"], wanted, strict=True)),
            "native mass properties do not corroborate the measured source geometry")


def state_refs(state, source_rows, status, equality):
    refs = state["references"]
    producer = refs["producer"]
    require(refs["passed"] and not refs.get("observation_error") and
            (producer["name"], producer["type"], producer["resolved_role"]) == ("AdditiveBox", "Extrusion", "AdditiveBox"),
            "the actual bound feature owner changed")
    rows = {(kind, role): row for kind, values in refs["by_kind"].items() for role, row in values.items()}
    require(rows.keys() == source_rows.keys() and refs["passed_counts"] == dict(Counter(kind for kind, _ in rows)),
            "live role inventory differs from the independent source-shape join")
    for key, row in rows.items():
        require(row["resolved_role"] == key[1] and row["touching_owned_faces"] == source_rows[key]["actual_incident_faces"],
                "the resolved body entity has a different role or producing face incidence")
    rows["producer", "AdditiveBox"] = producer
    return {key: (*reference(row, key[0], status, equality), row["baseline_reference_sha256"]) for key, row in rows.items()}


def inspect_phase(root, name, key, phase, identities):
    folder = PHASES[key][0]
    record = read(root, Path(name) / folder / "Record.json", phase["record_sha256"])
    require(record["passed"] and not record["first_failure"] and not record["cleanup_errors"] and
            record["job"] == {"role": folder, "input_sha256": phase["input_sha256"]} and
            record["result"] == {field: value for field, value in phase.items() if field != "record_sha256"}
            and phase["passed"] and phase["mechanics_passed"] and phase["immutable_input"] and
            phase["open_errors"] == phase["open_warnings"] == 0 and not phase["dialogs"] and not phase["controller_diagnostics"]
            and tuple(phase["states"]) == GEOMETRY_STATES[key], "candidate phase identity or mechanics changed")
    identities.add(verify_oracle(phase["oracle_identity"]))
    return tuple(PureWindowsPath(row["result"]) for row in record["api_calls"] if row["method"] == "GetPathName")


def transitions(states):
    baseline = states["Baseline"]
    by_state = {}
    for label, rows in states.items():
        sizes = {kind: Counter() for kind in (*KINDS, "producer")}
        for key, (_, size, captured) in rows.items():
            require(captured == baseline[key][0], "the lifecycle did not resolve the exact original captured token")
            sizes[key[0]][size] += 1
        by_state[label] = sizes
    by_transition = {}
    for before, after, changes, delta in (("Baseline", "Edited", False, 0), ("Edited", "Saved", True, 4), ("Saved", "FreshOpen", True, 0)):
        changed = Counter(dict.fromkeys((*KINDS, "producer"), 0))
        for key, (current, size, _) in states[after].items():
            original, old_size, _ = states[before][key]
            boundary = key[0] != "producer"
            require((current != original) == (changes and boundary) and size - old_size == (delta if boundary else 0),
                    "the measured transition changed the per-kind token byte/digest contrast")
            changed[key[0]] += int(current != original)
        by_transition[before + "To" + after] = {"digest_changes": changed, "boundary_token_byte_delta": delta, "producer_byte_delta": 0}
    return {"token_bytes_by_state": by_state, "transitions": by_transition}


def inspect_case(root, name, entry, source, edited_height, identities, status, equality, different):
    source_rows = original_roles(source)
    edit, reopen = entry["edit_save"], entry["fresh_reopen"]
    require(entry["original_fcstd_sha256"] == source["source"]["original_sha256"] and edit["input_sha256"] == source["generated_sha256"]
            and entry["prior_native_save_sha256"] == source["saved_sha256"] and
            entry["prior_native_record_sha256"] == source["native_lifecycle"]["original_native_phase_hashes"],
            "native candidate no longer binds the previously proved FreeCAD source and artifact")
    require(edit["height_edit"] == {"driver": DRIVERS[-1], "before_m": BASELINE_M[-1], "after_m": edited_height, "status": 0}
            and edit["save_status"] == [True, 0, 0] and edit["saved_sha256"] == reopen["input_sha256"],
            "the single edit or exact new native save/reopen chain changed")
    checked(root, Path(name) / "EditSave" / "Edited.SLDPRT", edit["saved_sha256"])
    first, saved = inspect_phase(root, name, "edit_save", edit, identities)
    reopened, = inspect_phase(root, name, "fresh_reopen", reopen, identities)
    require(first == PRIOR_WINDOWS / "Inputs" / name / "F14a.SLDPRT" and first != saved and saved == reopened,
            "exact original native or paired saved/open locators changed")
    states = {}
    for label, state in (edit["states"] | reopen["states"]).items():
        geometry(state, BASELINE_M if label in ("Initial", "Baseline") else (*BASELINE_M[:2], edited_height))
        require(state["tree"] == edit["states"]["Initial"]["tree"], "the ordered feature tree differs after the edit, save or reopen")
        if "references" in state:
            states[label] = state_refs(state, source_rows, status, equality)
    require(tuple(states) == PHASES["edit_save"][1] + PHASES["fresh_reopen"][1], "native reference stages changed")
    baseline = edit["states"]["Baseline"]["references"]
    distinct = baseline["distinct_role_checks"]
    require(baseline["distinct_comparison_passed"] and set(distinct) == set(KINDS) and
            all(row["passed"] and row["persistent_id_equality"] == different and len(set(row["roles"])) == 2 and
                all((kind, role) in source_rows for role in row["roles"]) for kind, row in distinct.items()),
            "an independent distinct-role comparison did not report different identity")
    require(len({row[0] for row in states["Baseline"].values()}) == 27, "distinct baseline byte digests collided inside a model")
    summary = {"original_fcstd_sha256": entry["original_fcstd_sha256"], "generated_sha256": edit["input_sha256"],
            "fresh_reopen_sha256": reopen["input_sha256"], "phase_records_sha256": [edit["record_sha256"], reopen["record_sha256"]],
            "source_body_xml_id": source["source"]["body_xml_id"], "source_primitive_xml_id": source["source"]["primitive_xml_id"],
            "source_shape_map_sha256": source["source"]["source_element_map_sha256"], "role_counts_by_state": edit["states"]["Baseline"]["references"]["passed_counts"] | {"producer": 1},
            "height_edit_m": [BASELINE_M[-1], edited_height],
            "distinct_role_equality": {kind: row["persistent_id_equality"] for kind, row in distinct.items()}}
    return summary, transitions(states)


def audit(root, packet):
    result = read(root, "Result.json", RESULT)
    probe = read(packet, "Probe.json", PROBE)
    require(result["schema"] == probe["schema"] == SCHEMA and result["packet_sha256"] == PROBE and
            result["prior_packet_sha256"] == probe["prior_sha256"] == PRIOR and probe["receipts_sha256"] == RECEIPTS and
            result["previous_capture_result_sha256"] == PREVIOUS_CAPTURE and result["pywin32_distribution_version"] == "312" and
            result["passed"] and result["controls_healthy"] and result["reference_transport_controls_passed"] and
            result["immutable_prior_inputs"] and result["oracle_idle_confirmed"] and tuple(result["cases"]) == CASES and
            result["heldout_inputs_read"] == result["writer_outputs_generated"] == result["complete_original_corpus_conversions"] == 0 and
            not result["source_reference_transfer_qualified"] and not result["public_writer_qualified"], "terminal v2 scope changed")
    for name, expected in probe["tools_sha256"].items():
        checked(packet, Path("Tools") / name, expected)
    for name, expected in RECEIPTS.items():
        checked(packet, name, expected)
    lineage = read(packet, LINEAGE, RECEIPTS[LINEAGE])
    api = result["registered_api"]
    prior = read(packet, "DrawingEdgeApiMetadata01.json", RECEIPTS["DrawingEdgeApiMetadata01.json"])
    require(api["wrapper_sha256"] == prior["wrapper_sha256"], "the registered 2026 COM wrapper differs")
    extension = api["members"]["IModelDocExtension"]
    methods = {name: extension[name][0]["member_id"] for name in ("GetPersistReference3", "GetObjectByPersistReference3", "IsSamePersistentID")}
    require(tuple(methods.values()) == (98, 101, 196), "the registered 2026 reference members changed")
    same, different = (api["enums"]["swObjectEquality"][name] for name in ("swObjectSame", "swObjectNotSame"))
    status = api["enums"]["swPersistReferencedObjectStates_e"]["swPersistReferencedObject_Ok"]
    require((status, same, different) == (0, 1, 0), "registered reference status and equality enums changed")
    identities = set()
    calibrations = controls(root, result, identities, status, same)
    measured = {name: inspect_case(root, name, result["cases"][name], lineage["cases"][name], height, identities, status, same, different)
                for name, height in zip(CASES, EDIT_HEIGHT_M, strict=True)}
    cases = {name: row for name, (row, _) in measured.items()}
    first, second = (state for _, state in measured.values())
    require(first == second, "the disclosed release pair no longer has the same observed state distributions")
    candidate_count = sum(sum(case["role_counts_by_state"].values()) for case in cases.values()) * len(first["token_bytes_by_state"])
    control_count = sum(len(row["self_resolved_token_bytes"]) for row in calibrations.values())
    require(len(identities) == result["distinct_native_processes"] == 6, "expected six separate exact native oracles")
    return {"schema": "kit.sw2026.f14a-live-persistence-proof.v1", "result_sha256": RESULT, "probe_sha256": PROBE,
            "previous_failed_result_sha256": PREVIOUS_CAPTURE, "source_lineage_receipt_sha256": RECEIPTS[LINEAGE],
            "oracle_build": "34.5.2.0604", "oracle_executable_sha256": ORACLE, "distinct_native_processes": len(identities),
            "registered_wrapper_sha256": api["wrapper_sha256"], "registered_reference_members": methods, "pywin32_distribution_version": "312",
            "transport": TRANSPORT, "matched_resolver_status": status, "matched_object_equality": same, "matched_persistent_id_equality": same,
            "controls": calibrations, "cases": cases, "per_case_reference_observations": first,
            "candidate_reference_resolutions": candidate_count, "control_reference_resolutions": control_count, "geometry_states": 12,
            "distinct_role_comparisons": 6, "downstream_live_persistence_passed": True,
            "source_reference_transfer_qualified": False, "public_writer_qualified": False,
            "native_processes_started_by_audit": 0, "heldout_inputs_read": 0, "corpus_conversions_counted": 0,
            "vendor_reference_bytes_emitted": 0}


def main():
    parser = ArgumentParser(description="Normalize the successful exact-build F14a live reference measurements")
    parser.add_argument("run", type=Path)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    value = audit(args.run.resolve(strict=True), args.packet.resolve(strict=True))
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    with args.output.open("xb") as file:
        file.write(data)
    print(json.dumps({"receipt_sha256": sha256(data).hexdigest(), "candidate_reference_resolutions": value["candidate_reference_resolutions"]}))


if __name__ == "__main__":
    main()
