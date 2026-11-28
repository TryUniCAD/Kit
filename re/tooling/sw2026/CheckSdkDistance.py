import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "re/tooling/sw2026"))

from CheckSdkPlanar import digest, freeze_source, write_json


def run_worker(root, output, request, tag):
    request_sha = write_json(output / f"{tag}Request.json", request)
    result = subprocess.run([sys.executable, "-I", "-B", str(root / "re/tooling/sw2026/SdkDistanceMateProcess.py")], cwd=root, input=json.dumps(request), capture_output=True, text=True, timeout=45)
    stdout, stderr = result.stdout.encode(), result.stderr.encode()
    (output / f"{tag}Stdout.json").write_bytes(stdout)
    (output / f"{tag}Stderr.txt").write_bytes(stderr)
    if result.returncode:
        raise ValueError(f"{tag} failed {result.returncode}: {result.stderr[-4000:]}")
    report = json.loads(stdout)
    if not report["passed"] or report["runtime_file_read_attempts"] != 0 or report["native_processes_started"] != 0:
        raise ValueError(f"{tag} failed its real process boundary")
    return report, {"request_sha256": request_sha, "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr), "exit_code": result.returncode, "worker_pid": report["worker_pid"], "entrypoint": "re/tooling/sw2026/SdkDistanceMateProcess.py"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root, manifest, source_sha = freeze_source(args.root.resolve(), output)
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(root), str(root / "src"), str(root / "re/tooling/sw2026"), str(root / "re/tooling/sw2026/serial")]
    from tests.Convert.Solidworks.Research.Mates.Distance.MakeDistInput import MakeDistInput
    from tests.Convert.Solidworks.Research.Mates.Distance.AssertDistGraph import AssertDistGraph
    from SdkDistanceBridge import EXTRA_FAULTS
    from SdkPlanarFaults import FAULT_NAMES
    cases, reports = [], {}
    for axis in "xyz":
        for index, length in enumerate((0.071375, 0.093625)):
            tag = f"Distance{axis.upper()}{index}"
            bundle = MakeDistInput(axis, length)
            sdk, sdk_identity = run_worker(root, output, {"mode": "sdk", "bundle": bundle}, tag + "Sdk")
            reference, reference_identity = run_worker(root, output, {"mode": "reference", "bundle": bundle}, tag + "Reference")
            AssertDistGraph(sdk, reference, length)
            reports[(axis, index)] = sdk
            constructor = {key: value for key, value in sdk["constructor"].items() if key != "sdk_mates_write"}
            cases.append({"case": tag, "passed": True, "whole_parent_container_identical": True, "all_parent_streams_identical": True, "whole_child_container_identical": True, "assembly": sdk["assembly"], "child": sdk["child"], "mate_stream": sdk["mate_stream"], "constructor": constructor, "readback": sdk["readback"], "sdk": sdk_identity, "reference": reference_identity})
    value_changes = []
    for axis in "xyz":
        first, second = reports[(axis, 0)], reports[(axis, 1)]
        changed = [name for name, value in first["assembly"]["streams"].items() if second["assembly"]["streams"][name] != value]
        if changed != ["Contents/Config-0-MatesList"] or first["child"] != second["child"]:
            raise ValueError("authored distance changed unrelated model streams")
        value_changes.append({"axis": axis, "before_metres": 0.071375, "after_metres": 0.093625, "changed_parent_streams": changed, "child_unchanged": True})
    negatives = []
    for index, fault in enumerate((*FAULT_NAMES, *EXTRA_FAULTS)):
        result, identity = run_worker(root, output, {"mode": "sdk", "bundle": MakeDistInput("y"), "fault": fault}, f"Reject{index:02}")
        if result.get("rejected") is not True or result["writer_output_count"] != 0 or not result["rejection"]["parent_state_unchanged"]:
            raise ValueError(f"malformed distance input was not atomically rejected: {fault}")
        negatives.append({"fault": fault, "passed": True, "rejection": result["rejection"], "identity": identity})
    for relative, item in manifest["files"].items():
        if digest((root / relative).read_bytes()) != item["sha256"]:
            raise ValueError("distance frozen code changed during execution")
    pids = [case[mode]["worker_pid"] for case in cases for mode in ("sdk", "reference")]
    pids.extend(case["identity"]["worker_pid"] for case in negatives)
    if len(pids) != len(set(pids)):
        raise ValueError("distance proof reused a worker process")
    report = {"schema": "kit.sw2026.sdk-distance-construction.v1", "passed": True, "source_manifest_sha256": source_sha, "source_files": len(manifest["files"]), "source_locked_before_generation": True, "source_unchanged": True, "positive_cases": cases, "value_changes": value_changes, "negative_cases": negatives, "distinct_worker_processes": len(pids), "runtime_input_file_read_attempts": 0, "native_processes_started": 0, "heldout_inputs_read": 0, "public_writer_enabled": False, "native_acceptance": False, "full_document_sdk_writer": False}
    report_sha = write_json(output / "SdkDistanceConstructionResults.json", report)
    print(json.dumps({"passed": True, "positive_cases": len(cases), "negative_cases": len(negatives), "distinct_worker_processes": len(pids), "source_manifest_sha256": source_sha, "report_sha256": report_sha}, sort_keys=True))


if __name__ == "__main__":
    main()
