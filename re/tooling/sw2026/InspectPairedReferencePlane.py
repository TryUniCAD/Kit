from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
import time


sys.path.insert(0, str(Path(__file__).resolve().parent))

from AuthorCurves import digest, require, write_json
from InspectGeneratedReferencePlane import ORACLE, SOURCE_LOCK_SHA256, TOOLS as BASE_TOOLS, checked, measure, predict


SCRIPT = Path(__file__).resolve()
SCHEMA = "kit.sw2026.paired-offset-plane-native-trial.v1"
TOOLS = (*BASE_TOOLS, "ReferencePlaneSourceRecipe.py", SCRIPT.name)


def verify(path, sha):
    root = path.parent.resolve(strict=True)
    job = json.loads(checked(path, sha, root).read_bytes())
    require(path.name == "PairedTrial.json" and job["schema"] == SCHEMA and job["source_lock_sha256"] == SOURCE_LOCK_SHA256
            and job["oracle_sha256"] == ORACLE and job["heldout_inputs_read"] == 0 and job["native_acceptance"] is False,
            "another paired discovery identity was supplied")
    require(SCRIPT.parent == root / "Tools" and set(job["tool_hashes"]) == set(TOOLS)
            and set(job["tool_hashes"]) == {item.name for item in SCRIPT.parent.glob("*.py")}, "use the exact frozen paired observer")
    for name, expected in job["tool_hashes"].items():
        checked(root / "Tools" / name, expected, root / "Tools")
    checked(root / "SourceLock.json", SOURCE_LOCK_SHA256, root)
    checked(root / "ApiMetadata.json", job["api_metadata_sha256"], root)
    manifest = json.loads(checked(root / "CodeManifest.json", job["code_manifest_sha256"], root).read_bytes())
    code = root / "CodeRoot"
    for name, expected in manifest["files_sha256"].items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts and relative.suffix == ".py", "invalid frozen source entry")
        checked(code / relative, expected, code)
    require(set(manifest["files_sha256"]) == {item.relative_to(code).as_posix() for item in code.rglob("*.py")},
            "the complete paired writer closure changed")
    for directory in (code, code / "src", code / "re/tooling/sw2026", code / "re/tooling/sw2026/serial"):
        sys.path.insert(0, str(directory))
    from ReferencePlaneSourceRecipe import source_prediction, source_request
    from ReferencePlaneSourcePlan import disclosed_cases

    case = json.loads(checked(root / "Case.json", job["case_sha256"], root).read_bytes())
    require(case in disclosed_cases(), "the paired observer admits only the original disclosed authored specifications")
    request = json.loads(checked(root / "Request.json", job["request_sha256"], root).read_bytes())
    expected = json.loads(checked(root / "Expected.json", job["prediction_sha256"], root).read_bytes())
    require(expected == source_prediction(case) and request == source_request(case, Path(job["guest_root"]) / "GeneratedInput")
            and predict(request, case["edit_distance_m"]) == expected["native_observer_prediction"],
            "paired request or independent prediction differs from the authored source recipe")
    require(job["control"]["prediction"] == job["generated"]["prediction"] == expected["native_observer_prediction"]
            and job["generated"]["edit_distance_m"] == case["edit_distance_m"], "the source and generated models do not share their authored semantics")
    for role, directory in (("control", "Controls"), ("generated", "FrozenGenerated")):
        entry = job[role]
        require(Path(entry["filename"]).name == entry["filename"] and entry["filename"] == case["name"] + ".SLDPRT"
                and checked(root / directory / entry["filename"], entry["sha256"], root).stat().st_size == entry["bytes"],
                "a paired native input changed")
    require(job["state"] in ("prepared", "frozen") and job["execution_enabled"] is (job["state"] == "frozen"),
            "paired preparation is distinct from native execution")
    require(job["state"] != "frozen" or re.fullmatch(r"[0-9a-f]{40}", job["writer_revision"] or ""),
            "native execution requires the actual committed writer identity")
    return job


def differences(before, after):
    return [{"index": index, "source": before[index] if index < len(before) else None,
             "generated": after[index] if index < len(after) else None}
            for index in range(max(len(before), len(after)))
            if index >= len(before) or index >= len(after) or before[index] != after[index]]


def paired_identity(source, generated):
    checks = {"complete_ordered_native_tree_equal": source["feature_tree"] == generated["feature_tree"],
              "plane_constraint_and_types_equal": all(source["plane"][name] == generated["plane"][name]
                                                       for name in ("constraint", "type", "type2", "parents")),
              "native_plane_frame_equal": source["plane"]["transform"] == generated["plane"]["transform"],
              "native_sketch_origin_and_normal_equal": all(source[name] == generated[name]
                                                           for name in ("sketch_world_origin", "sketch_world_normal")),
              "native_body_count_equal": source["body_count"] == generated["body_count"]}
    for role in ("plane", "radius"):
        first, second = source["dimension_bindings"][role], generated["dimension_bindings"][role]
        symbolic = ("name", "full_name", "driving", "editable", "unit_basis", "owner_identity", "creation_identity", "matching_display_count")
        checks[role + "_exact_parameter_identity"] = all(first[name] == second[name] for name in symbolic)
        first_displays = [{key: value for key, value in row.items() if key != "value_m"} for row in first["display_traversal"]]
        second_displays = [{key: value for key, value in row.items() if key != "value_m"} for row in second["display_traversal"]]
        checks[role + "_exact_display_bindings"] = first_displays == second_displays
    checks["driving_values_match"] = all(math.isclose(source["driving_dimensions_m"][name], value, rel_tol=5e-7, abs_tol=1e-12)
                                         for name, value in generated["driving_dimensions_m"].items())
    return {"passed": all(checks.values()), "checks": checks,
            "source_nodes": len(source["feature_tree"]), "generated_nodes": len(generated["feature_tree"]),
            "tree_differences": differences(source["feature_tree"], generated["feature_tree"])}


def run(path, sha):
    require(os.name == "nt", "the paired native trial runs only in the root-owned Windows guest")
    root, job = path.parent, verify(path, sha)
    require(job["execution_enabled"] is True and job["state"] == "frozen", "the prepared paired plan has not been released for native execution")
    require(Path(job["guest_root"]).samefile(root), "actual paired native custody differs from the encoded generated path")
    inspection = root / "Inspection"
    inspection.mkdir(exist_ok=False)
    inputs = [root / "Controls" / job["control"]["filename"], root / "FrozenGenerated" / job["generated"]["filename"],
              root / "GeneratedInput" / job["generated"]["filename"]]
    immutable = {item: digest(item) for item in inputs}
    require(immutable[inputs[1]] == immutable[inputs[2]] == job["generated"]["sha256"], "actual generated custody differs from the frozen candidate")
    result = {"schema": SCHEMA, "packet_sha256": sha, "passed": False, "phases": [], "started_at": time.time(),
              "source_generated_paired_acceptance": False, "heldout_inputs_read": 0}
    record = inspection / "PairedReferencePlaneResults.json"

    def phase(role, entry, source, edited=False):
        row = {"role": role, "passed": False, "started_at": time.time()}
        result["phases"].append(row)
        write_json(record, result)
        row.update(measure(job, root, role, entry, source, edited), finished_at=time.time())
        write_json(record, result)
        return row

    try:
        before = phase("ControlBefore", job["control"], inputs[0])
        if before["passed"]:
            generated = phase("Generated", job["generated"], inputs[2])
            if generated["passed"]:
                result["source_generated_identity"] = paired_identity(before["rebuilt"], generated["rebuilt"])
                result["generated_initial_edit_tree_equal"] = generated["rebuilt"]["feature_tree"] == generated["edited"]["feature_tree"]
                saved = generated["saved"]
                target = checked(root / "Saved" / saved["filename"], saved["sha256"], root / "Saved")
                reopened = phase("Reopen", job["generated"] | {"sha256": saved["sha256"]}, target, True)
                result["generated_edit_reopen_tree_equal"] = bool(reopened["passed"] and
                    reopened["rebuilt"]["feature_tree"] == generated["edited"]["feature_tree"])
                require(digest(target) == saved["sha256"], "fresh native reopening changed the edited sibling")
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        try:
            after = phase("ControlAfter", job["control"], inputs[0])
            if result["phases"][0]["passed"] and after["passed"]:
                result["source_bracket_identity"] = paired_identity(result["phases"][0]["rebuilt"], after["rebuilt"])
        except Exception as error:
            result["control_after_exception"] = repr(error)
        result["controls_healthy"] = [row["passed"] for row in result["phases"] if row["role"].startswith("Control")] == [True, True]
        result["immutable_inputs_unchanged"] = all(item.is_file() and digest(item) == expected for item, expected in immutable.items())
        identities = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in result["phases"]}
        result["distinct_processes"] = sum(type(value) is int and value > 0 for value in identities)
        result["native_phases_distinct_and_ordered"] = bool(len(result["phases"]) == result["distinct_processes"] == 4 and
            all(first["finished_at"] <= second["started_at"] for first, second in zip(result["phases"], result["phases"][1:])))
        result["source_generated_paired_acceptance"] = bool(result.get("source_generated_identity", {}).get("passed") and
            result.get("source_bracket_identity", {}).get("passed") and result.get("generated_initial_edit_tree_equal") and
            result.get("generated_edit_reopen_tree_equal"))
        result["passed"] = bool(result["native_phases_distinct_and_ordered"] and all(row["passed"] for row in result["phases"])
                                and result["source_generated_paired_acceptance"] and result["controls_healthy"]
                                and result["immutable_inputs_unchanged"] and not result.get("exception"))
        result["finished_at"] = time.time()
        write_json(record, result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    try:
        path = args.packet.resolve(strict=True)
        if args.mode == "verify":
            job = verify(path, args.packet_sha256)
            print(json.dumps({"verified_packet": args.packet_sha256, "state": job["state"], "execution_enabled": job["execution_enabled"],
                              "heldout_inputs_read": 0, "native_processes_started": 0}))
            return 0
        result = run(path, args.packet_sha256)
        print(json.dumps({key: result[key] for key in ("passed", "controls_healthy", "distinct_processes", "source_generated_paired_acceptance")}))
        return int(not result["passed"])
    except Exception:
        print(json.dumps({"passed": False, "heldout_inputs_read": 0, "native_processes_started": 0}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
