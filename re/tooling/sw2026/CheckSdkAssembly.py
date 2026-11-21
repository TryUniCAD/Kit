import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from CheckSdkPlanar import digest, freeze_source, write_json
from CheckHeaderEpoch import compare_old


def worker(root, output, request, tag, entrypoint):
    data = json.dumps(request, separators=(",", ":"), allow_nan=False).encode()
    (output / (tag + "Request.json")).write_bytes(data)
    result = subprocess.run([sys.executable, "-I", "-B", str(root / "re/tooling/sw2026" / entrypoint), str(root)], cwd=root,
                            input=data, capture_output=True, timeout=120)
    (output / (tag + "Stdout.json")).write_bytes(result.stdout)
    (output / (tag + "Stderr.txt")).write_bytes(result.stderr)
    if result.returncode:
        raise ValueError(f"{tag} failed {result.returncode}: {result.stderr.decode()[-4000:]}")
    report = json.loads(result.stdout)
    if not report["passed"] or report["runtime_input_file_reads"] or report["native_acceptance"] or report["public_writer_qualified"]:
        raise ValueError("SDK assembly failed the declared isolated process boundary")
    return report, {"exact_stdin_sha256": digest(data), "request_bytes": len(data), "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr),
                    "exit_code": result.returncode, "worker_pid": report["worker_pid"], "entrypoint": entrypoint}


def one_case(root, output, request, tag):
    built, build_id = worker(root, output, request, tag + "Build", "SdkAssemblyProcess.py")
    projected = {"request": request, "build": built}
    prepared, prepare_id = worker(root, output, projected, tag + "Prepare", "SdkAssemblyVerify.py")
    counterpart, counterpart_id = worker(root, output, projected, tag + "Counterpart", "SdkAssemblyCounterpart.py")
    return {"case": tag, "passed": True, "kind": request["mate"]["kind"], "axis": request["mate"]["axis"],
            "assembly": {key: built["assembly"][key] for key in ("bytes", "sha256", "stream_order")},
            "child": {key: built["child"][key] for key in ("bytes", "sha256", "stream_order")},
            "streams": prepared["assembly"], "round_trips": prepared["round_trips"], "checks": prepared["checks"],
            "next_id": built["next_id"], "wrapper_next_id": built["wrapper_next_id"], "file_handles": built["file_handles"],
            "actual_child_identity": built["actual_child_identity"], "child_bytes_unchanged": built["child_bytes_unchanged"],
            "same_as_independent_research": counterpart["same_as_independent_research"], "build": build_id, "prepare": prepare_id, "counterpart": counterpart_id}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--planar-proof", type=Path)
    parser.add_argument("--distance-proof", type=Path)
    parser.add_argument("--baseline-proof", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root, source, source_sha = freeze_source(args.root.resolve(), output)
    sys.path[:0] = [str(root), str(root / "src"), str(root / "re/tooling/sw2026")]
    from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmCase import MakeAsmCase
    from SdkAssemblyFaults import FAULTS
    positives = []
    for kind in ("coincident", "parallel", "distance"):
        for axis in "xyz":
            for variant in (False, True):
                tag = kind.title() + axis.upper() + ("Beta" if variant else "Alpha")
                positives.append(one_case(root, output, MakeAsmCase(kind, axis, variant), tag))
    negatives = []
    for index, fault in enumerate(FAULTS):
        request = MakeAsmCase("coincident", "y", False)
        request["fault"] = fault
        report, identity = worker(root, output, request, f"Reject{index:02}", "SdkAssemblyProcess.py")
        if not report.get("rejected") or report["writer_output_count"] or not report["child_bytes_unchanged"]:
            raise ValueError("SDK assembly failed its negative publication boundary")
        negatives.append({"case": fault, "passed": True, "exception": report["exception"], "diagnostic": report["diagnostic"], "child_bytes_unchanged": True, "writer_output_count": 0, "identity": identity})
    regressions = []
    for kind, prior in (("planar", args.planar_proof), ("distance", args.distance_proof)):
        if prior is not None:
            regressions.append(compare_old(root, output, prior, kind, source))
    for name, row in source["files"].items():
        if digest((root / name).read_bytes()) != row["sha256"]:
            raise ValueError("SDK assembly source changed during frozen process proof")
    pids = [row[phase]["worker_pid"] for row in positives for phase in ("build", "prepare", "counterpart")]
    pids.extend(row["identity"]["worker_pid"] for row in negatives)
    pids.extend(row["identity"]["worker_pid"] for group in regressions for row in group["cases"])
    if len(pids) != len(set(pids)):
        raise ValueError("SDK assembly proof reused a worker identity")
    baseline_sha = None
    if args.baseline_proof is not None:
        baseline_bytes = (args.baseline_proof / "SdkAssemblyResults.json").read_bytes()
        baseline = json.loads(baseline_bytes)
        baseline_sha = digest(baseline_bytes)
        for current, old in zip(positives, baseline["positive_cases"], strict=True):
            if any(current[key] != old[key] for key in ("case", "assembly", "child", "streams", "checks", "next_id", "wrapper_next_id")):
                raise ValueError("complete generated bundle changed against the explicitly pinned prior proof")
    report = {"schema": "kit.sw2026.sdk-complete-assembly.v1", "passed": True, "source_manifest_sha256": source_sha,
              "source_files": len(source["files"]), "source_locked_before_generation": True, "source_unchanged": True,
              "positive_cases": positives, "negative_cases": negatives, "published_regressions": regressions,
              "distinct_worker_processes": len(pids), "typed_stream_round_trips": sum(row["round_trips"] for row in positives),
              "baseline_process_result_sha256": baseline_sha, "baseline_all_eighteen_bundles_identical": baseline_sha is not None,
              "runtime_input_file_reads": 0, "native_processes_started": 0, "heldout_inputs_read": 0, "public_writer_enabled": False, "native_acceptance": False}
    report_sha = write_json(output / "SdkAssemblyResults.json", report)
    print(json.dumps({"passed": True, "source_manifest_sha256": source_sha, "report_sha256": report_sha, "positive_cases": len(positives), "negative_cases": len(negatives),
                      "published_regressions": sum(len(group["cases"]) for group in regressions), "distinct_worker_processes": len(pids), "round_trips": report["typed_stream_round_trips"]}, sort_keys=True))


if __name__ == "__main__":
    main()
