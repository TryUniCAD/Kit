import argparse
import hashlib
import json
import pathlib
import subprocess
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    data = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    path.write_bytes(data)
    return digest(data)


def freeze_source(root, output):
    code_root = output / "CodeRoot"
    code_root.mkdir()
    files = {}
    for directory in ("src", "re/tooling/sw2026", "tests/Convert/Solidworks/Research"):
        for path in sorted((root / directory).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            relative = path.relative_to(root)
            data = path.read_bytes()
            target = code_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            files[relative.as_posix()] = {"sha256": digest(data), "bytes": len(data)}
    for relative in ("tests/__init__.py", "tests/Convert/__init__.py", "tests/Convert/Solidworks/__init__.py"):
        path = root / relative
        if path.is_file():
            data = path.read_bytes()
            target = code_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            files[relative] = {"sha256": digest(data), "bytes": len(data)}
    manifest = {"schema": "kit.sw2026.sdk-planar-source.v1", "files": files, "vendor_payloads_copied": 0, "native_inputs_read": 0, "source_locked_before_generation": True}
    sha = write_json(output / "SourceManifest.json", manifest)
    return code_root, manifest, sha


def run_worker(root, output, request, tag):
    request_sha = write_json(output / f"{tag}Request.json", request)
    result = subprocess.run([sys.executable, "-I", "-B", str(root / "re/tooling/sw2026/SdkPlanarMateProcess.py")], cwd=root, input=json.dumps(request), text=True, capture_output=True, timeout=45)
    stdout = result.stdout.encode()
    stderr = result.stderr.encode()
    (output / f"{tag}Stdout.json").write_bytes(stdout)
    (output / f"{tag}Stderr.txt").write_bytes(stderr)
    if result.returncode:
        raise ValueError(f"{tag} failed {result.returncode}: {result.stderr[-4000:]}")
    report = json.loads(stdout)
    if report["runtime_file_read_attempts"] != 0 or report["native_processes_started"] != 0 or not report["passed"]:
        raise ValueError(f"{tag} failed its process boundary")
    return report, {"request_sha256": request_sha, "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr), "exit_code": result.returncode, "worker_pid": report["worker_pid"]}


def compare_case(root, output, bundle, tag):
    sdk, sdk_identity = run_worker(root, output, {"mode": "sdk", "bundle": bundle}, tag + "Sdk")
    reference, reference_identity = run_worker(root, output, {"mode": "reference", "bundle": bundle}, tag + "Reference")
    for key in ("assembly", "child", "mate_stream", "readback"):
        if sdk[key] != reference[key]:
            raise ValueError(f"{tag} differs in {key}")
    constructor = {key: value for key, value in sdk["constructor"].items() if key != "sdk_mates_write"}
    for key in ("independent_transform_caches", "distinct_resolved_wrappers", "distinct_detached_wrappers", "exclusive_detached_components", "parent_owner_identity", "actual_occurrence_backlinks"):
        if constructor[key] is not True:
            raise ValueError(f"{tag} lost {key}")
    mate_stream = {key: value for key, value in sdk["mate_stream"].items() if key not in ("read_coverage", "write_coverage")}
    coverage = {}
    for mode in ("read", "write"):
        value = sdk["mate_stream"][mode + "_coverage"]
        if not value["completed"] or any(value[key] for key in ("missing_schemas", "provisional_schemas", "native_byte_fields")):
            raise ValueError(f"{tag} has unqualified {mode} coverage")
        coverage[mode] = value
    return {"case": tag, "passed": True, "whole_parent_container_identical": True, "all_parent_streams_identical": True, "whole_child_container_identical": True, "mate_stream": mate_stream, "assembly": sdk["assembly"], "child": sdk["child"], "constructor": constructor, "readback": sdk["readback"], "coverage": coverage, "sdk": sdk_identity, "reference": reference_identity}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root, manifest, source_sha = freeze_source(args.root.resolve(), output)
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(root), str(root / "src"), str(root / "re/tooling/sw2026")]
    from tests.Convert.Solidworks.Research.Mates.Construction.MakeSdkMate import MakeSdkMate
    from SdkPlanarFaults import FAULT_NAMES
    cases = []
    for kind in ("coincident", "parallel"):
        for axis in "xyz":
            tag = kind.title() + axis.upper()
            cases.append(compare_case(root, output, MakeSdkMate(kind, axis), tag))
    negatives = []
    for index, fault in enumerate(FAULT_NAMES):
        result, identity = run_worker(root, output, {"mode": "sdk", "bundle": MakeSdkMate("coincident", "y"), "fault": fault}, f"Reject{index:02}")
        if result.get("rejected") is not True or result["writer_output_count"] != 0 or not result["rejection"]["parent_state_unchanged"]:
            raise ValueError(f"construction did not reject {fault} atomically")
        negatives.append({"fault": fault, "passed": True, "rejection": result["rejection"], "identity": identity})
    for relative, item in manifest["files"].items():
        if digest((root / relative).read_bytes()) != item["sha256"]:
            raise ValueError("frozen source changed during construction proof")
    pids = [case[mode]["worker_pid"] for case in cases for mode in ("sdk", "reference")]
    pids += [case["identity"]["worker_pid"] for case in negatives]
    if len(pids) != len(set(pids)):
        raise ValueError("construction proof did not use distinct fresh worker processes")
    report = {"schema": "kit.sw2026.sdk-planar-construction.v1", "passed": True, "source_manifest_sha256": source_sha, "source_files": len(manifest["files"]), "source_unchanged": True, "source_locked_before_generation": True, "positive_cases": cases, "negative_cases": negatives, "distinct_worker_processes": len(pids), "runtime_input_file_read_attempts": 0, "native_processes_started": 0, "heldout_inputs_read": 0, "public_writer_enabled": False, "native_acceptance": False, "full_document_sdk_writer": False}
    report_sha = write_json(output / "SdkPlanarConstructionResults.json", report)
    print(json.dumps({"passed": True, "positive_cases": len(cases), "negative_cases": len(negatives), "distinct_worker_processes": len(pids), "source_manifest_sha256": source_sha, "report_sha256": report_sha}, sort_keys=True))


if __name__ == "__main__":
    main()
