import json
import math
import os
from pathlib import Path
from shutil import copyfile
import sys

from AuthorCurves import digest, require, write_json
from InspectCombinedPlanarMates import phase, signature
from InspectSdkPlanarGroup import CONTROL_CHILD, CONTROL_PARENT, observe_options
from OriginalPlanarEvaluation import SCHEMA, SLOTS, checked, verify
from RunOriginalPlanarEvaluation import execute, progress
from SdkPlanarGroupPrediction import predict, state_matches


def paired_mass(source, generated):
    result = {}
    for role in ("mass", "child_mass"):
        first, second = source[role], generated[role]
        result[role] = all(math.isclose(a, b, rel_tol=5e-7, abs_tol=1e-12) for a, b in zip([first["volume"], first["area"], first["mass"], *first["com"]], [second["volume"], second["area"], second["mass"], *second["com"]], strict=True))
    return result


def prepared(packet, wanted, slot, stage_sha):
    job, locators, rows, source_root, control = verify(packet, wanted)
    target = Path(locators["private_guest_root"]) / slot
    stage = json.loads(checked(target / "StagePacket.json", stage_sha).read_bytes())
    require(stage["schema"] == "kit.sw2026.original-planar-prepared-slot.v1" and stage["slot"] == slot and stage["evaluation_sha256"] == wanted and stage["passed"] and stage["native_acceptance"] is False, "the original slot lacks its exact prepared source/recipe lock")
    request = json.loads(checked(target / "NeutralRequest.json", stage["request_sha256"]).read_bytes())
    expected = json.loads(checked(target / "Prediction.json", stage["prediction_sha256"]).read_bytes())
    checked(target / "AuthoredNames.json", stage["names_sha256"])
    freeze = json.loads(checked(target / "RequestFreeze.json", stage["request_freeze_sha256"]).read_bytes())
    require(freeze["constructor_invocations"] == 0 and freeze["request_sha256"] == stage["request_sha256"] and freeze["prediction_sha256"] == stage["prediction_sha256"] and predict(request, expected["case"], expected["edit_distance_m"]) == expected, "the independent original-slot prediction was not frozen before construction")
    locked = rows[SLOTS[slot]]
    require(stage["source"] == {"parent": locators["slots"][slot]["parent_guest_path"], "parent_sha256": locked["native_sha256"], "child": locators["slots"][slot]["child_guest_path"], "child_sha256": locked["synchronized_child"]["native_sha256"]}, "the original source paths or immutable hashes differ from the public lock")
    source_paths = (checked(Path(stage["source"]["parent"]), locked["native_sha256"]), checked(Path(stage["source"]["child"]), locked["synchronized_child"]["native_sha256"]))
    for kind, row in stage["generated_files"].items():
        checked(target / "FrozenGenerated" / row["file"], row["sha256"])
        require(Path(row["encoded_path"]).parent == target / "GeneratedInput" and Path(row["encoded_path"]).name == row["file"], "the generated slot escaped its exact private working directory")
    controls = (checked(Path(locators["control"]["parent_guest_path"]), CONTROL_PARENT), checked(Path(locators["control"]["child_guest_path"]), CONTROL_CHILD))
    return job, locators, source_root, control, target, stage, request, expected, source_paths, controls


def run(packet, wanted, slot, stage_sha, progress_path):
    require(os.name == "nt", "original source native measurement runs only in the root-owned Windows oracle")
    job, locators, source_root, control, target, stage, request, expected, source_paths, controls = prepared(packet, wanted, slot, stage_sha)
    output = target / "Inspection"
    output.mkdir()
    phases = {}
    report = {"schema": SCHEMA, "slot": slot, "evaluation_sha256": wanted, "stage_packet_sha256": stage_sha,
              "phases": phases, "heldout_source_exposed": True, "heldout_slots_evaluated": 1, "passed": False}
    native_job = {"case": expected["case"], "child_size_m": [.04, .02, .01], "edit_distance_m": expected["edit_distance_m"]}
    control_expected = {"case": control["case"], "assembly_configuration": "Default", "child_configuration": "Default",
                        "child_parameters_m": {"D1@Sketch1": .04, "D2@Sketch1": .02, "D1@Boss-Extrude1": .01},
                        "occurrence_names": ["CohortChild-" + str(index + 1) for index in range(len(control["case"]["placements"]))]}

    def record(role, selected, edit, chosen, options, **extra):
        progress(progress_path, slot, role, "running")
        row = phase(selected, edit, role, *chosen, output / role, observe=lambda author, model, child: observe_options(author, model, child, options), **extra)
        phases[role] = row
        write_json(output / "Result.json", report)
        progress(progress_path, slot, role, "passed" if row["passed"] else "failed", native_process_identity=row.get("oracle_identity", {}), private_record_sha256=row.get("record_sha256"))
        return row

    try:
        before = record("ControlBefore", control, control["case"], controls, control_expected)
        if before["passed"]:
            original = record("Original", native_job, expected["case"], source_paths, expected)
            if original["passed"]:
                work = target / "GeneratedInput"
                work.mkdir()
                for row in stage["generated_files"].values():
                    copyfile(target / "FrozenGenerated" / row["file"], Path(row["encoded_path"]))
                    checked(Path(row["encoded_path"]), row["sha256"])
                paths = tuple(Path(stage["generated_files"][key]["encoded_path"]) for key in ("assembly", "child"))
                generated = record("Generated", native_job, expected["edited_case"], paths, expected, editing=True)
                if generated["passed"]:
                    reopened = record("FreshReopen", native_job, expected["edited_case"], paths, expected, reopened=generated["saved"])
                    a, b = signature(original["rebuilt"]), signature(generated["rebuilt"])
                    report["source_generated_identity"] = {key: a[key] == b[key] for key in a}
                    report["source_generated_mass"] = paired_mass(original["rebuilt"], generated["rebuilt"])
                    report["exact_prediction"] = bool(all(state_matches(row[key], expected["initial"], expected) for row in (original, generated) for key in ("initial", "rebuilt")) and state_matches(generated["edited"], expected["edited"], expected) and all(state_matches(reopened[key], expected["edited"], expected) for key in ("initial", "rebuilt")))
                    report["edit_identity_preserved"] = signature(generated["rebuilt"]) == signature(generated["edited"])
                    report["reopen_identity_preserved"] = signature(generated["edited"]) == signature(reopened["rebuilt"])
                    if reopened["passed"]:
                        progress(progress_path, slot, "saved_sdk_readback", "running")
                        public, public_id = execute(source_root, output, "ReadSdkPlanarGroupNative.py", "SavedPublicRead", extra=("read", "--root", str(source_root), "--file", str(paths[0])))
                        sys.path[:0] = [str(source_root), str(source_root / "src")]
                        from interchange import CadDocument
                        from ReadSdkPlanarGroupNative import compare

                        comparison = compare(CadDocument.from_json(public["document_json"]), expected, True, generated["saved"]["child"]["native_sha256"])
                        audits = {}
                        for kind, path in zip(("assembly", "child"), paths, strict=True):
                            audit, identity = execute(source_root, output, "ReadSdkPlanarGroupNative.py", "SavedAudit" + kind, extra=("audit", "--root", str(source_root), "--file", str(path)))
                            audits[kind] = {"result": audit, "identity": identity}
                        checked(paths[0], generated["saved"]["parent"])
                        checked(paths[1], generated["saved"]["child"]["native_sha256"])
                        report["saved_public_readback"] = {"comparison": comparison, "identity": public_id, "audits": audits}
    except Exception as error:
        report["error"] = repr(error)
    finally:
        after = record("ControlAfter", control, control["case"], controls, control_expected)
        report["controls_healthy"] = bool(phases.get("ControlBefore", {}).get("passed") and after["passed"])
        report["control_identity_preserved"] = bool(report["controls_healthy"] and signature(phases["ControlBefore"]["rebuilt"]) == signature(after["rebuilt"]))
        report["source_and_frozen_inputs_unchanged"] = False
        report["saved_files_unchanged_after_readback"] = False
        try:
            prepared(packet, wanted, slot, stage_sha)
            report["source_and_frozen_inputs_unchanged"] = True
            saved = phases.get("Generated", {}).get("saved")
            if saved:
                checked(Path(stage["generated_files"]["assembly"]["encoded_path"]), saved["parent"])
                checked(Path(stage["generated_files"]["child"]["encoded_path"]), saved["child"]["native_sha256"])
                report["saved_files_unchanged_after_readback"] = True
        except Exception as error:
            report["custody_error"] = repr(error)
        report["distinct_processes"] = len({row["oracle_identity"]["process_creation_filetime"] for row in phases.values() if row.get("oracle_identity")})
        report["numeric_checks"] = sum(row.get("numeric_checks", 0) for row in phases.values())
        report["passed"] = bool(list(phases) == ["ControlBefore", "Original", "Generated", "FreshReopen", "ControlAfter"] and report["distinct_processes"] == 5 and all(row["passed"] for row in phases.values()) and report["control_identity_preserved"] and report["source_and_frozen_inputs_unchanged"] and report["saved_files_unchanged_after_readback"] and report.get("exact_prediction") and all(report.get("source_generated_identity", {"missing": False}).values()) and all(report.get("source_generated_mass", {"missing": False}).values()) and report.get("edit_identity_preserved") and report.get("reopen_identity_preserved") and report.get("saved_public_readback", {}).get("comparison", {}).get("passed"))
        report["vendor_loadable"] = report["passed"]
        report["application_usable"] = report["passed"]
        write_json(output / "Result.json", report)
        summary = {"schema": "kit.sw2026.original-planar-public-slot-result.v1", "slot": slot, "passed": report["passed"], "native_result_sha256": digest(output / "Result.json"),
                   "stage_packet_sha256": stage_sha, "source_and_frozen_inputs_unchanged": report["source_and_frozen_inputs_unchanged"], "saved_files_unchanged_after_readback": report["saved_files_unchanged_after_readback"], "controls_healthy": report["controls_healthy"], "distinct_processes": report["distinct_processes"],
                   "numeric_checks": report["numeric_checks"], "heldout_source_exposed": True, "heldout_slots_evaluated": 1,
                   "source_generated_identity": report.get("source_generated_identity", {}), "source_generated_mass": report.get("source_generated_mass", {}),
                   "exact_prediction": report.get("exact_prediction", False), "edit_identity_preserved": report.get("edit_identity_preserved", False), "reopen_identity_preserved": report.get("reopen_identity_preserved", False),
                   "saved_public_readback_passed": bool(report.get("saved_public_readback", {}).get("comparison", {}).get("passed")),
                   "frozen_generated_sha256": {key: row["sha256"] for key, row in stage["generated_files"].items()},
                   "vendor_loadable": report["passed"], "application_usable": report["passed"], "public_assembly_writer_enabled": False}
        progress(progress_path, slot, "complete", "passed" if report["passed"] else "failed", summary=summary)
    return summary
