from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from itertools import product
from pathlib import Path
import json

from ReferencePacket import CASES, ORACLE, require, read, verify_oracle


F14A_RESULT = "6bc759f108d1d4da3c771ec1841f2c70e868c8c1a68cb9934fd71a7de5d4d7f3"
F14A_PACKET = "8345fc169780226487529c3d020a9da10ea4e95f36344e6949614895adf394a5"
FILLET_RECEIPT = "e7573a71c5fb709a26ae512a332f3fe6eecca5fef949b8f98380ac7cbd1337f3"
PHASES = {"edit_save": ("EditSave", ("Baseline", "Edited", "Saved")), "fresh_reopen": ("FreshReopen", ("FreshOpen",))}
KINDS = {"face": (2, "swSelFACES", 2), "edge": (1, "swSelEDGES", 1), "vertex": (0, "swSelVERTICES", 3)}
REFUSAL = {"exception_type": "EvidenceFailure", "reason": "selected object returned no bounded persistent reference"}


def failed_capture(row):
    require(row["stage"] == "capture_reference" and not row["passed"] and row["error"] == REFUSAL and
            not ({"reference", "resolver_status", "persistent_id_equality", "reference_transport"} & row.keys()),
            "expected the exact unexplained return guard failure before the resolver")


def audit_roles(state, enums):
    refs = state["references"]
    require(not refs["passed"] and not refs.get("observation_error") and refs["by_kind"].keys() == KINDS.keys() and
            refs["passed_counts"] == dict.fromkeys(KINDS, 0), "the terminal role inventory changed")
    by_kind = {}
    for kind, (stars, enum_name, enum_value) in KINDS.items():
        rows = refs["by_kind"][kind]
        roles = {"".join(role) for role in product("01*", repeat=3) if role.count("*") == stars}
        require(rows.keys() == roles and enums["swSelectType_e"][enum_name] == enum_value,
                "the exact role keys or registered selection type changed")
        for name, row in rows.items():
            touching = sorted("".join(flag if index == axis else "*" for index in range(3))
                              for axis, flag in enumerate(name) if flag != "*")
            require(row["selected_type"] == enum_value and row["selected_object_equality"] == enums["swObjectEquality"]["swObjectSame"]
                    and row["touching_owned_faces"] == touching, "the actual selected role or its creator ownership changed")
            failed_capture(row)
        by_kind[kind] = {"selected_and_owned": len(roles), "capture_guard_refusals": len(roles), "resolver_calls": 0}
    producer = refs["producer"]
    require((producer["name"], producer["type"]) == ("AdditiveBox", "Extrusion"), "another native producer was selected")
    failed_capture(producer)
    return by_kind | {"producer": {"name": "AdditiveBox", "capture_guard_refusals": 1, "resolver_calls": 0}}


def audit_f14a(root):
    result = read(root, "Result.json", F14A_RESULT)
    require(result["schema"] == "kit.sw2026.f14a-live-references.v1" and result["packet_sha256"] == F14A_PACKET and
            not result["passed"] and result["controls_healthy"] and result["immutable_prior_inputs"] and
            result["oracle_idle_confirmed"] and result["heldout_inputs_read"] == result["writer_outputs_generated"] == 0,
            "expected the original completed F14a capture-guard failure")
    identities = set()
    controls = {}
    for key, folder in (("control_before", "ControlBefore"), ("control_after", "ControlAfter")):
        control = result[key]
        record = read(root, Path(folder) / "Record.json", control["record_sha256"])
        require(control["passed"] and control["oracle_identity"] == record["oracle_identity"] and record["opened"] and record["rebuilt"]
                and record["open_errors"] == record["open_warnings"] == record["whats_wrong"] == 0,
                "original healthy bracket changed")
        identities.add(verify_oracle(record["oracle_identity"]))
        controls[key] = control["record_sha256"]
    references = result["registered_api"]
    cases = {}
    require(tuple(result["cases"]) == CASES, "unexpected disclosed case roster")
    for name, case in result["cases"].items():
        observed = cases[name] = {}
        for key, (folder, labels) in PHASES.items():
            phase = case[key]
            record = read(root, Path(name) / folder / "Record.json", phase["record_sha256"])
            require(not record["passed"] and record["first_failure"] is None and not record["cleanup_errors"] and
                    record["result"] == {key: value for key, value in phase.items() if key != "record_sha256"} and
                    not phase["passed"] and phase["mechanics_passed"] and phase["immutable_input"] and
                    phase["open_errors"] == phase["open_warnings"] == 0 and not phase["dialogs"] and not phase["controller_diagnostics"],
                    "native mechanics or phase custody changed")
            identities.add(verify_oracle(phase["oracle_identity"]))
            states = {label: audit_roles(state, references["enums"]) for label, state in phase["states"].items() if "references" in state}
            require(tuple(states) == labels, "unexpected reference phase progression")
            observed[key] = {"record_sha256": phase["record_sha256"], "input_sha256": phase["input_sha256"], "states": states}
        edit, reopened = case["edit_save"], case["fresh_reopen"]
        require(edit["save_status"] == [True, 0, 0] and edit["saved_sha256"] == reopened["input_sha256"],
                "the native save and fresh reopen do not have the same proven file identity")
    require(len(identities) == result["distinct_native_processes"] == 6, "the six exact native process identities changed")
    role_rows = [row for case in cases.values() for phase in case.values() for state in phase["states"].values() for row in state.values()]
    return {"result_sha256": F14A_RESULT, "probe_sha256": F14A_PACKET, "passed": False, "controls_healthy": True,
            "native_processes": len(identities), "immutable_inputs": True, "control_records_sha256": controls,
            "captured_return_metadata": False, "capture_guard_failed_before_any_native_resolution": True,
            "capture_guard_refusals": sum(row["capture_guard_refusals"] for row in role_rows),
            "resolved_reference_calls": sum(row["resolver_calls"] for row in role_rows),
            "registered_wrapper_sha256": references["wrapper_sha256"],
            "registered_members": references["members"]["IModelDocExtension"], "cases": cases}


def audit_fillet(root, receipt):
    prior = read(receipt.parent.resolve(strict=True), receipt.name, FILLET_RECEIPT)
    require(prior["oracle_sha256"] == ORACLE and prior["oracle_build"] == "34.5.2.0604" and prior["passed"],
            "unexpected prior disclosed native control")
    cases = {}
    totals = Counter()
    for name, phases in prior["source_phase_receipt_sha256"].items():
        cases[name] = {}
        for phase, digest in phases.items():
            record = read(root, Path(name) / phase / "Record.json", digest)
            require(record["passed"] and record["first_failure"] is None and not record["cleanup_errors"],
                    "prior native fillet call is unqualified")
            verify_oracle(record["oracle_identity"])
            counts = Counter()
            for row in record["api_calls"]:
                if row["method"] == "GetPersistReference3":
                    require(set(row["result"]) == {"returned_object"} and row["arguments"]["binding"] == "untyped-method",
                            "the recorded return envelope is outside the same COM transport")
                    counts[row["result"]["returned_object"]] += 1
            require(counts.keys() == {"memoryview"}, "the exact prior native binary-buffer class changed")
            totals.update(counts)
            cases[name][phase] = {"record_sha256": digest, "observed_return_types": counts}
    require(totals == {"memoryview": 56}, "the exact prior native buffer sample count changed")
    return {"receipt_sha256": FILLET_RECEIPT, "native_source_lock_sha256": prior["source_lock_sha256"],
            "observed_return_types": totals, "cases": cases}


def main():
    parser = ArgumentParser(description="Normalize the disclosed F14a capture refusal and exact-build reference transport control")
    parser.add_argument("failed_run", type=Path)
    parser.add_argument("disclosed_fillet_capture", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = Path(__file__).resolve().parents[3] / "solidworks/measurements/2026/EdgeFilletArchiveRead01.json"
    result = {"schema": "kit.sw2026.f14a-live-reference-capture-audit.v1", "oracle_build": "34.5.2.0604", "oracle_sha256": ORACLE,
              "native_processes_started_by_audit": 0, "protected_inputs_read": 0, "vendor_reference_bytes_emitted": 0,
              "source_reference_transfer_qualified": False, "native_reference_persistence_qualified": False,
              "failed_f14a_capture": audit_f14a(args.failed_run.resolve(strict=True)),
              "independent_native_byte_transport": audit_fillet(args.disclosed_fillet_capture.resolve(strict=True), receipt)}
    data = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    with args.output.open("xb") as file:
        file.write(data)
    print(json.dumps({"sanitized_receipt_sha256": sha256(data).hexdigest(), "native_processes_started": 0}))


if __name__ == "__main__":
    main()
