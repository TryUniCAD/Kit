import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026"), str(ROOT / "re/tooling/sw2026/serial")]

from CheckSdkPlanar import digest, freeze_source, write_json


FAULTS = ("duplicate_log", "invalid_epoch", "overflow_epoch", "boolean_epoch", "wrong_log_class", "wrong_stamp_class", "wrong_log_schema", "wrong_stamp_schema", "invalid_items", "wrong_count", "wrong_list_owner", "bad_row")


def run_worker(root, output, request, tag, entrypoint="HeaderEpochProcess.py"):
    stdin_text = json.dumps(request, allow_nan=False)
    stdin_bytes = stdin_text.encode("utf-8")
    (output / f"{tag}Request.json").write_bytes(stdin_bytes)
    request_sha = digest(stdin_bytes)
    canonical_sha = write_json(output / f"{tag}CanonicalRequest.json", request)
    result = subprocess.run([sys.executable, "-I", "-B", str(root / "re/tooling/sw2026" / entrypoint)], cwd=root, input=stdin_text, text=True, capture_output=True, timeout=45)
    stdout, stderr = result.stdout.encode(), result.stderr.encode()
    (output / f"{tag}Stdout.json").write_bytes(stdout)
    (output / f"{tag}Stderr.txt").write_bytes(stderr)
    if result.returncode:
        raise ValueError(f"{tag} failed {result.returncode}: {result.stderr[-4000:]}")
    report = json.loads(stdout)
    if not report["passed"] or report["runtime_file_read_attempts"] or report["native_processes_started"]:
        raise ValueError(f"{tag} failed the generated process boundary")
    return report, {"request_sha256": request_sha, "exact_stdin_sha256": request_sha, "canonical_request_sha256": canonical_sha, "request_bytes": len(stdin_bytes), "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr), "exit_code": result.returncode, "worker_pid": report["worker_pid"], "entrypoint": entrypoint}


def compare_old(root, output, prior, kind, source):
    from tests.Convert.Solidworks.Research.Mates.Construction.MakeSdkMate import MakeSdkMate
    from tests.Convert.Solidworks.Research.Mates.Distance.MakeDistInput import MakeDistInput

    name = "SdkPlanarConstructionResults.json" if kind == "planar" else "SdkDistanceConstructionResults.json"
    entrypoint = "SdkPlanarMateProcess.py" if kind == "planar" else "SdkDistanceMateProcess.py"
    raw_bytes = (prior / name).read_bytes()
    report = json.loads(raw_bytes)
    prior_source = json.loads((prior / "SourceManifest.json").read_bytes())
    dependencies = ["tests/Convert/Solidworks/Research/Assembly/OccurrenceInput.py", "tests/Convert/Solidworks/Research/Assembly/RootRequest.py", "tests/Convert/Solidworks/Research/FreshPartInput.py", "tests/Convert/Solidworks/Research/Mates/Construction/MateDesigns.py", "tests/Convert/Solidworks/Research/Mates/Construction/MakeSdkMate.py"]
    if kind != "planar":
        dependencies.append("tests/Convert/Solidworks/Research/Mates/Distance/MakeDistInput.py")
    for relative in dependencies:
        if prior_source["files"][relative] != source["files"][relative]:
            raise ValueError("historical request factory changed; do not infer its original object order")
    if not report["passed"] or report["native_acceptance"] or report["heldout_inputs_read"]:
        raise ValueError("old regression inputs must be the published generated source-only proof")
    cases = []
    for case in report["positive_cases"]:
        request_bytes = (prior / f"{case['case']}SdkRequest.json").read_bytes()
        if digest(request_bytes) != case["sdk"]["request_sha256"]:
            raise ValueError("published generated request changed")
        archived = json.loads(request_bytes)
        spec, = archived["bundle"]["mates"]
        axis = archived["bundle"]["child"]["document"]["plane_axis"]
        bundle = MakeSdkMate(spec["kind"], axis) if kind == "planar" else MakeDistInput(axis, spec["distance_m"])
        request = {"mode": "sdk", "bundle": bundle}
        canonical = (json.dumps(request, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        if canonical != request_bytes:
            raise ValueError("historical authored request values changed")
        current, identity = run_worker(root, output, request, f"Prior{kind.title()}{case['case']}", entrypoint)
        for key in ("assembly", "child", "readback"):
            if current[key] != case[key]:
                raise ValueError(f"published {kind} {case['case']} changed in {key}")
        for key in ("bytes", "sha256", "map_base", "map_terminal"):
            if current["mate_stream"][key] != case["mate_stream"][key]:
                raise ValueError("published mate stream changed")
        cases.append({"case": case["case"], "passed": True, "historical_authored_order_restored": True, "canonical_values_equal_archived_request": True, "whole_parent_identical": True, "all_parent_streams_identical": True, "whole_child_identical": True, "mate_stream_identical": True, "typed_readback_identical": True, "assembly": current["assembly"], "child": current["child"], "identity": identity})
    return {"kind": kind, "prior_raw_sha256": digest(raw_bytes), "unchanged_request_factory_files": {relative: source["files"][relative] for relative in dependencies}, "cases": cases}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--planar-proof", type=Path, required=True)
    parser.add_argument("--distance-proof", type=Path, required=True)
    parser.add_argument("--common-dimensions", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root, source, source_sha = freeze_source(args.root.resolve(), output)
    common_bytes = args.common_dimensions.read_bytes()
    common = json.loads(common_bytes)
    for item in common["files"]:
        if source["files"].get(item["path"]) != {"sha256": item["sha256"], "bytes": item["bytes"]}:
            raise ValueError("shared dimension source differs from its exact frozen extraction")
    sys.path[:0] = [str(root), str(root / "src"), str(root / "re/tooling/sw2026"), str(root / "re/tooling/sw2026/serial")]
    from tests.Convert.Solidworks.Research.Mates.HeaderEpoch.MakeEpochProbe import MakeEpochProbe
    regression = [compare_old(root, output, args.planar_proof, "planar", source), compare_old(root, output, args.distance_proof, "distance", source)]
    cases = []
    for axis in "xyz":
        for scenario in ("absent", "empty", "authored"):
            tag = axis.upper() + scenario.title()
            reference, reference_id = run_worker(root, output, MakeEpochProbe(axis, scenario, "body", ModeValue="reference"), tag + "Reference")
            views = []
            for view in ("body", "sdk"):
                current, identity = run_worker(root, output, MakeEpochProbe(axis, scenario, view), tag + view.title())
                for key in ("assembly", "child", "mate_stream", "readback"):
                    if current[key] != reference[key]:
                        raise ValueError(f"{tag} {view} changed {key}")
                if current["constructor"]["header_epoch"]["actual_log_identities_preserved"] is not True:
                    raise ValueError("header projection replaced actual log nodes")
                views.append({"view": view, "passed": True, "whole_parent_identical": True, "all_parent_streams_identical": True, "whole_child_identical": True, "mate_stream_identical": True, "actual_log_identities_preserved": True, "identity": identity})
            cases.append({"axis": axis, "case": scenario, "passed": True, "assembly": reference["assembly"], "child": reference["child"], "mate_stream": reference["mate_stream"], "readback": reference["readback"], "reference": reference_id, "views": views})
    negatives = []
    for view in ("body", "sdk"):
        for index, fault in enumerate(FAULTS):
            current, identity = run_worker(root, output, MakeEpochProbe("y", "authored", view, FaultValue=fault), f"Reject{view.title()}{index:02}")
            if current.get("rejected") is not True or current["writer_output_count"] or not current["rejection"]["parent_state_unchanged"]:
                raise ValueError("header epoch failed atomic rejection")
            negatives.append({"view": view, "fault": fault, "passed": True, "rejection": current["rejection"], "identity": identity})
    for relative, item in source["files"].items():
        if digest((root / relative).read_bytes()) != item["sha256"]:
            raise ValueError("header source changed during verification")
    pids = [case["identity"]["worker_pid"] for group in regression for case in group["cases"]]
    pids.extend(case["reference"]["worker_pid"] for case in cases)
    pids.extend(view["identity"]["worker_pid"] for case in cases for view in case["views"])
    pids.extend(case["identity"]["worker_pid"] for case in negatives)
    if len(pids) != len(set(pids)):
        raise ValueError("header proof reused a process identity")
    if args.common_dimensions.read_bytes() != common_bytes:
        raise ValueError("shared dimension manifest changed during verification")
    report = {"schema": "kit.sw2026.sdk-header-epoch-integration.v1", "passed": True, "source_manifest_sha256": source_sha, "source_files": len(source["files"]), "source_unchanged": True, "source_locked_before_generation": True, "common_dimensions_manifest_sha256": digest(common_bytes), "published_regressions": regression, "header_cases": cases, "negative_cases": negatives, "distinct_worker_processes": len(pids), "runtime_input_file_read_attempts": 0, "native_processes_started": 0, "heldout_inputs_read": 0, "public_writer_enabled": False, "native_acceptance": False}
    report_sha = write_json(output / "HeaderEpochResults.json", report)
    print(json.dumps({"passed": True, "source_manifest_sha256": source_sha, "report_sha256": report_sha, "published_bundle_regressions": sum(len(group["cases"]) for group in regression), "header_cases": len(cases), "negative_cases": len(negatives), "distinct_worker_processes": len(pids)}, sort_keys=True))


if __name__ == "__main__":
    main()
