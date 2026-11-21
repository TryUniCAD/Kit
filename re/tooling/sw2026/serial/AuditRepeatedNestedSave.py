from __future__ import annotations

import argparse
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

from AuditGeneratedNestedSave import projection, validate_targets
from AuthorCurves import digest, require
from Classes import registry
from NestedAssemblySourcePlan import ORACLE, checked
from SyncedAssemblies import typed_header
from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm
from convert.adapters.solidworks.Container.Container import SldprtArchive


SCRIPT = Path(__file__).resolve()
PACKET_SHA = "13c6f53da57a592e12304281f4cd6b025a60b5aab6f1df23ea3748d29c49cde1"
RESULT_SHA = "eded243a834ae840c9e77b9effcfe5cb2a4c95318c299c67debbcd77e2dd6501"


def additional_checks(documents, paths, prediction, reg, edited):
    managers = {name: typed_header(SldprtArchive.from_bytes(path.read_bytes()), reg, "Contents/CMgr", "moConfigurationMgr_c") for name, path in paths.items()}
    by_name = {row["model"]["f18"]["f08"]: key for key, row in documents.items()}
    for key, document in documents.items():
        uses = Counter(id(ref["f3b0"]) for ref in document["refs"])
        for reference, state in zip(document["refs"], document["state"].get("references", ()), strict=True):
            child_key = by_name[state["target"]]
            child = documents[child_key]
            config = managers[child_key]["f360"]
            expected_kind = 2 if child["model"].cls == "moPart_c" else 3
            require(reference["f3c0"] == {"f08": config["f18"]["f08"], "f10": config["f08"]} and
                    state["child_kind"] == expected_kind and state["directory_uses"] == uses[id(reference["f3b0"])],
                    "saved mixed directory kind, selected configuration or direct target user count differs")
            require(not edited or state["target_local_bounds_byte_equal"], "saved occurrence local box differs from its actual saved target")
            state["target_configuration_exact"] = True
        if document["model"].cls == "moAssembly_c":
            xml = DecodeNativeAsm(SldprtArchive.from_bytes(paths[key].read_bytes()))
            wanted = prediction["definitions"][key]["edited" if edited else "initial"]
            require(len(xml.occurrence_paths) == wanted["total_occurrences"] and document["state"]["activity_count"] == wanted["total_occurrences"],
                    "saved expanded XML paths or active configuration count differ from the independent graph")
            document["state"]["xml"] = {"definitions": len(xml.definitions), "local_occurrence_rows": len(xml.occurrences), "expanded_paths": len(xml.occurrence_paths)}


def native_receipt(root, packet, result, prediction, audit):
    phases = []
    for row, file in zip(result["phases"], ("Before01Host.json", "Generated01Host.json", "Reopen01Host.json", "After01Host.json"), strict=True):
        transport = json.loads((root / file).read_bytes())
        require(transport["transport_returncode"] == transport["supervisor_exit_code"] == 0 and transport["transport_exit_confirmed"] is True,
                "native repeated phase transport did not finish cleanly")
        record = root / "Inspection" / row["mode"] / "Record.json"
        require(digest(record) == row["record_sha256"] and row["open_errors"] == row["open_warnings"] == 0 and row["passed"] is True,
                "native repeated record changed or warned")
        state = {key: row[key] for key in ("mode", "passed", "open_errors", "open_warnings", "record_sha256", "started_at", "finished_at")}
        state.update(transport_sha256=digest(root / file), transport_exit_code=0,
                     native_process_creation_filetime=row["oracle_identity"]["process_creation_filetime"])
        if row["mode"] in ("before", "after"):
            require(row["source_files_unchanged"] is True, "disclosed native source files changed")
            state["source_files_unchanged"] = True
        else:
            for label in ("initial", "rebuilt", "edited"):
                if label not in row:
                    continue
                scene = row[label]
                wanted = prediction["definitions"][prediction["root"]]["edited" if label == "edited" or row["mode"] == "reopen" else "initial"]
                measured = scene["definitions"][prediction["root"]]["mass_properties"]
                state[label] = {"expanded_paths": scene["total_occurrences"], "body_count": scene["body_count"], "expected": {
                    key: wanted[key] for key in ("volume", "area", "com")}, "measured": {key: measured[key] for key in ("volume", "area", "com")}}
            if "saved_files" in row:
                state["saved_files"] = row["saved_files"]
        phases.append(state)
    edited = result["phases"][1]["edited"]["definitions"]
    reopened = result["phases"][2]["initial"]["definitions"]
    require(all(edited[key]["tree"] == reopened[key]["tree"] for key in edited), "generated definition tree changed after save and fresh reopen")
    encoded = json.dumps(audit, sort_keys=True, indent=2, allow_nan=False) + "\n"
    typed = {role: {key: {name: row[name] for name in ("config_header_geometry_stamp", "config_header_transform_stamp", "headers", "activity_count")}
                    for key, row in documents.items()} for role, documents in audit["documents"].items()}
    return {"schema": "kit.sw2026.generated-repeated-nested-native-persistence.v1", "generated_profile_native_passed": True,
            "native_acceptance": False, "production_corpus_conversions": 0, "heldout_inputs_read": 0,
            "packet_sha256": PACKET_SHA, "raw_native_result_sha256": RESULT_SHA, "writer_revision": result["writer_revision"],
            "writer_tool_sha256": result["writer_tool_sha256"], "observer_tool_sha256": packet["tool_sha256"], "oracle_sha256": ORACLE,
            "oracle_file_version": "34.5.2.0604", "source_lock_sha256": result["source_lock_sha256"],
            "prediction_sha256": result["prediction_sha256"], "controls_healthy": True, "distinct_processes": 4,
            "bracket_order_verified": True, "generated_input_files_immutable": True, "synchronized_derivative_files_match": True,
            "definition_trees_preserved_on_reopen": True, "frozen_generated_files": packet["files"], "phases": phases,
            "typed_saved_audit": {"tool_sha256": audit["tool_sha256"], "receipt_sha256": sha256(encoded.encode()).hexdigest(),
                                  "stream_round_trips": audit["stream_round_trips"], "target_states_and_configs_exact": True,
                                  "direct_directory_users_exact": True, "saved_child_local_bounds_byte_equal": True,
                                  "states": typed},
            "limitations": ["Disclosed Default-configuration rigid prism hierarchy", "Separate sealed evaluation pending",
                            "Generated header construction and native saved header lifecycle remain distinct", "Public adapter writing remains unqualified"]}


def main():
    parser = argparse.ArgumentParser(description="Audit the exact disclosed repeated generated bundle and its four native saved derivatives")
    parser.add_argument("trial", type=Path)
    parser.add_argument("--native-receipt", action="store_true")
    args = parser.parse_args()
    root = args.trial.resolve(strict=True)
    require(root.name == "GeneratedRepeatedNestedAssembly01", "use the exact disclosed repeated generated trial")
    packet = json.loads(checked(root / "Trial.json", PACKET_SHA, root).read_bytes())
    result = json.loads(checked(root / "Inspection/NestedAssemblyResults.json", RESULT_SHA, root).read_bytes())
    prediction = json.loads(checked(root / "Expected.json", packet["prediction_sha256"], root).read_bytes())
    require(result["passed"] and result["controls_healthy"] and result["distinct_processes"] == 4 and result["oracle_sha256"] == ORACLE and
            result["packet_sha256"] == PACKET_SHA and result["heldout_inputs_read"] == 0, "the repeated native result is not qualified")
    saved = result["phases"][1]["saved_files"]
    reopened = result["phases"][2]["initial"]["definitions"]
    require(set(saved) == set(packet["files"]) == set(reopened) and all(row["status"] == [True, 0, 0] and row["sha256"] == reopened[key]["sha256"]
                                                                       for key, row in saved.items()), "repeated native save and reopen closures differ")
    reg = registry()
    reports = {}
    for role, edited in (("FrozenGenerated", False), ("GeneratedInput", True)):
        files = saved if edited else packet["files"]
        paths = {key: root / role / packet["files"][key]["file"] for key in files}
        documents = {key: projection(paths[key], value, reg) for key, value in files.items()}
        validate_targets(documents, prediction, edited)
        additional_checks(documents, paths, prediction, reg, edited)
        reports[role] = {key: document["state"] for key, document in documents.items()}
    audit = {"schema": "kit.sw2026.generated-repeated-nested-save-typed-audit.v1", "tool_sha256": digest(SCRIPT),
             "packet_sha256": PACKET_SHA, "raw_native_result_sha256": RESULT_SHA, "writer_revision": result["writer_revision"],
             "typed_audit_passed": True, "stream_round_trips": sum(len(row["streams"]) for role in reports.values() for row in role.values()),
             "heldout_inputs_read": 0, "native_files_written": 0, "documents": reports}
    report = native_receipt(root, packet, result, prediction, audit) if args.native_receipt else audit
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
