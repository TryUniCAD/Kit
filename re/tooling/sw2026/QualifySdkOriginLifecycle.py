from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()



def component_binding(row, display):
    records = display["component_reference_closure"]
    owners = {record["identity"]["object_index"]: record for record in records}
    if len(owners) != len(records):
        return False
    def fields(identity, kind):
        if identity.get("class") != kind or identity.get("schema") != 1 or identity.get("concrete_runtime_class") is not True:
            raise ValueError("profile component path is not a concrete current owner")
        record = owners[identity["object_index"]]
        if record["identity"] != identity:
            raise ValueError("profile component path identity differs")
        return record["fields"]
    try:
        chain = fields(display["wrapper_fields"]["f58"], "moChainComponent_c")
        reference = fields(chain["f20"], "moReferenceChain_c")
        targets = fields(reference["f08"], "moExtFeatureList_c")
        if reference["f24"] != 0 or targets["n"] != len(targets["f08"]) or targets["n"] != 1:
            return False
        external = fields(targets["f08"][0]["o"], "moExtFeature_c")
        return external["f50"] == row["actual_view_internal_reference"] and chain["owner"] == row["view_reference_fields"]["owner"] and display["display_fields"]["f40"] == row["actual_view"] and display["display_fields"]["f48"] == display["component_profile"]
    except (KeyError, TypeError, ValueError):
        return False


def path_config_binding(row, case):
    declared = row["declared_reference_file"]
    configurations = row["child_configuration_metadata"]["configurations"]
    selector = row["view_reference_fields"]["f3c0"]
    name = selector["f08"]
    if isinstance(name, dict):
        if name.get("kind") != "CString":
            return False
        name = name["text"]
    return declared.get("available") is True and PureWindowsPath(declared["native_file_path"]) == PureWindowsPath(case["paths"]["child"]) and len(configurations) == 1 and configurations[0]["name"] == name == case["configuration"] and configurations[0]["native_object_id"] == selector["f10"] and configurations[0]["selected_by_f360"] is True and configurations[0]["selected_by_f368"] is True

def main():
    parser = argparse.ArgumentParser(description="Join disclosed generated native origin lifecycles to their actual typed child profiles")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--native-result-sha256", required=True)
    args = parser.parse_args()
    root = args.packet.parent.resolve(strict=True)
    if args.output.exists() or digest(args.packet) != args.packet_sha256 or digest(args.candidate / "SourceManifest.json") != args.manifest_sha256:
        raise ValueError("use immutable source and packet identities with an unused output")
    packet = json.loads(args.packet.read_bytes())
    if packet["source_manifest_sha256"] != args.manifest_sha256:
        raise ValueError("native packet source closure differs")
    native_path = root / "Inspection/Result.json"
    if digest(native_path) != args.native_result_sha256:
        raise ValueError("native lifecycle result changed")
    native = json.loads(native_path.read_bytes())
    if native["packet_sha256"] != args.packet_sha256 or native["passed"] is not True or native["controls_healthy"] is not True or native["distinct_native_processes"] != 18:
        raise ValueError("native lifecycle lacks complete healthy process evidence")
    observer = root / "HostTools/InspectDrawingProfileChild.py"
    if digest(observer) != packet["host_tools"]["InspectDrawingProfileChild.py"]["sha256"] or Path(__file__).resolve() != root / "HostTools/QualifySdkOriginLifecycle.py" or digest(Path(__file__)) != packet["host_tools"][Path(__file__).name]["sha256"]:
        raise ValueError("frozen actual child observer or qualifier changed")
    args.output.mkdir(parents=True)
    report = {"schema": "kit.sw2026.sdk-origin-disclosed-native-qualification.v1", "packet_sha256": args.packet_sha256,
              "native_result_sha256": args.native_result_sha256, "source_manifest_sha256": args.manifest_sha256,
              "states": [], "passed": False, "hidden_inputs_read": 0, "heldout_acceptance": False,
              "original_source_output_verdict_changed": False, "public_drawing_writer_enabled": False}
    for state, phase in (("initial", "open-save"), ("edited", "edit-move-save")):
        pairs = []
        expected_ids = {}
        for case in packet["cases"]:
            row = native["phases"][case["name"] + "/" + phase]
            if not row["passed"]:
                raise ValueError("native case is incomplete")
            fields = {}
            for kind, key in (("drawing", "drawing_file"), ("child", "child_file")):
                item = row[key]
                path = (root / item["relative_path"]).resolve(strict=True)
                if not path.is_relative_to(root) or digest(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
                    raise ValueError("saved native derivative custody differs")
                fields[kind] = {"path": str(path), "sha256": item["sha256"], "bytes": item["bytes"]}
            pairs.append({"case": case["name"], "role": state, **fields, "orientation": case["view"]["orientation"],
                          "declared_expected_native_resolved_path": case["paths"]["child"]})
            expected_ids[case["name"]] = row["saved"]["child"]["profile_ids"]["origin"]
        pair_path = args.output / (state + "Pairs.json")
        pair_path.write_text(json.dumps({"schema": "kit.sw2026.disclosed-profile-child-pairs.v1", "pairs": pairs}, indent=2) + "\n")
        observed_path = args.output / (state + "Profiles.json")
        result = subprocess.run([sys.executable, "-I", "-B", str(observer), str(args.candidate), str(pair_path), str(observed_path),
                                 "--manifest-sha256", args.manifest_sha256, "--pairs-sha256", digest(pair_path)], capture_output=True, timeout=300)
        (args.output / (state + ".stdout.txt")).write_bytes(result.stdout)
        (args.output / (state + ".stderr.txt")).write_bytes(result.stderr)
        if result.returncode != 0:
            report["states"].append({"state": state, "passed": False, "return_code": result.returncode})
            continue
        actual = json.loads(observed_path.read_bytes())
        if actual.get("data_collected") is not True or actual.get("source_immutable") is not True or len(actual["cases"]) != 4:
            report["states"].append({"state": state, "passed": False, "diagnostic": "typed observation incomplete"})
            continue
        case_lookup = {case["name"]: case for case in packet["cases"]}
        for row in actual["cases"]:
            displays = row.get("profile_displays", [])
            passed = row.get("drawing_definition_byte_identity") is True and row.get("observation_complete") is True and row.get("drawing_unchanged") is True and row.get("child_unchanged") is True
            matched = passed and row.get("child_config_complete") is True and row.get("child_resolved_complete") is True and len(displays) == 1 and path_config_binding(row, case_lookup[row["case"]])
            if matched:
                display = displays[0]
                target = display.get("actual_child_profile")
                matched = target is not None and target["class"] == "moOriginProfileFeature_c" and target["schema"] == 1 and target["concrete_runtime_class"] is True and target["native_f08"] == expected_ids[row["case"]]
                matched = matched and display.get("creation_log_epoch_equal") is True and display.get("actual_child_id_match_count") == 1 and component_binding(row, display)
            report["states"].append({"case": row["case"], "state": state, "passed": bool(matched),
                                      "actual_native_origin_id": expected_ids[row["case"]], "raw_report_sha256": digest(observed_path),
                                      "complete_definition_byte_identity": passed})
    report["passed"] = len(report["states"]) == 8 and all(row["passed"] for row in report["states"])
    report["disclosed_native_origin_lifecycle_qualified"] = report["passed"]
    out = args.output / "Result.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": report["passed"], "result_sha256": digest(out), "heldout_acceptance": False}))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
