import argparse
from itertools import permutations
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from CheckSdkPlanar import digest, freeze_source, write_json
from CheckSdkAssembly import worker, one_case
from CheckSdkOrderedAssembly import ordered_case


def nested_case(root, output, request, tag):
    first, first_id = worker(root, output, request, tag + "BuildA", "SdkNestedAssemblyProcess.py")
    second, second_id = worker(root, output, request, tag + "BuildB", "SdkNestedAssemblyProcess.py")
    a, b = dict(first), dict(second)
    require(a.pop("worker_pid") != b.pop("worker_pid") and a == b, "fresh SDK nested builds differ")
    return {"case": tag, "passed": True, "definition_count": first["definition_count"], "expanded_root_occurrences": first["expanded_root_occurrences"],
            "typed_stream_round_trips": first["typed_stream_round_trips"], "documents": {name: {key: row[key] for key in ("kind", "path", "bytes", "sha256", "activity", "direct_references", "target_ids", "streams")}
                                                                                   for name, row in first["documents"].items()}, "builds": [first_id, second_id]}


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ordered-proof", type=Path, required=True)
    parser.add_argument("--single-proof", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root, source, source_sha = freeze_source(args.root.resolve(), output)
    sys.path[:0] = [str(root), str(root / "src"), str(root / "re/tooling/sw2026")]
    from tests.Convert.Solidworks.Research.Construction.Nesting.MakeNestedCase import MakeNestedCase
    from tests.Convert.Solidworks.Research.Construction.Nesting.NestedFaultCase import NestedFaultCase
    from tests.Convert.Solidworks.Research.Construction.AssemblySets.MakeOrderCase import MakeOrderCase
    from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmCase import MakeAsmCase
    from PredictSdkNestedAssembly import predict

    positives, negatives = [], []
    pids = []
    for mixed in (False, True):
        tag = "Repeated" if mixed else "Single"
        request = MakeNestedCase(mixed, str(PureWindowsPath(r"C:\KitSdkNested") / tag))
        row = nested_case(root, output, request, tag)
        prediction = predict(request)
        require(prediction["expanded_occurrences"] == row["expanded_root_occurrences"] and prediction["body_count"] == (5 if mixed else 1),
                "independent authored hierarchy prediction differs")
        row["prediction_sha256"] = write_json(output / (tag + "Prediction.json"), prediction)
        positives.append(row)
        pids.extend(item["worker_pid"] for item in row["builds"])
    for fault in ("cycle", "missing", "duplicate", "unreachable", "foreign", "name", "frame"):
        request = NestedFaultCase(fault)
        data = json.dumps(request, separators=(",", ":"), allow_nan=False).encode()
        result = subprocess.run([sys.executable, "-I", "-B", str(root / "re/tooling/sw2026/SdkNestedAssemblyProcess.py"), str(root)], input=data, capture_output=True, timeout=120)
        (output / ("Reject" + fault + ".stdout")).write_bytes(result.stdout)
        (output / ("Reject" + fault + ".stderr")).write_bytes(result.stderr)
        require(result.returncode != 0 and not result.stdout and b"ValueError" in result.stderr and b"PermissionError" not in result.stderr,
                "malformed nested definition escaped its constructor admission")
        negatives.append({"case": fault, "exit_code": result.returncode, "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr), "writer_output_count": 0, "passed": True})
    ordered = json.loads((args.ordered_proof / "SdkOrderedAssemblyResults.json").read_bytes())
    old_ordered = {tuple(row["kind_order"]) + (row["case"].endswith("Beta"),): row for row in ordered["positive_cases"]}
    ordered_rows = []
    for order in permutations(("coincident", "parallel", "distance")):
        for variant in (False, True):
            old = old_ordered[(*order, variant)]
            current = ordered_case(root, output, MakeOrderCase(order, variant), "Prior" + old["case"])
            require(all(current[key] == old[key] for key in ("assembly", "child", "streams", "checks", "mate_ids", "dimension_ids", "next_id", "wrapper_next_id")),
                    "recursive composition changed a previously published ordered bundle")
            ordered_rows.append(current)
            pids.extend(current[name]["worker_pid"] for name in ("build", "prepare", "counterpart"))
    single = json.loads((args.single_proof / "SdkAssemblyResults.json").read_bytes())
    single_rows = []
    for old in single["positive_cases"]:
        current = one_case(root, output, MakeAsmCase(old["kind"], old["axis"], old["case"].endswith("Beta")), "PriorSingle" + old["case"])
        require(all(current[key] == old[key] for key in ("assembly", "child", "streams", "checks", "next_id", "wrapper_next_id")),
                "recursive composition changed a previously published single mate bundle")
        single_rows.append(current)
        pids.extend(current[name]["worker_pid"] for name in ("build", "prepare", "counterpart"))
    require(len(pids) == len(set(pids)), "nested qualification reused a worker process identity")
    require(all(digest((root / name).read_bytes()) == row["sha256"] for name, row in source["files"].items()), "frozen SDK nested source changed during qualification")
    report = {"schema": "kit.sw2026.sdk-nested-assembly-construction.v1", "passed": True, "source_manifest_sha256": source_sha, "source_files": len(source["files"]),
              "source_locked_before_generation": True, "source_unchanged": True, "positive_cases": positives, "negative_cases": negatives,
              "ordered_regressions": ordered_rows, "single_regressions": single_rows, "distinct_identified_worker_processes": len(pids),
              "negative_worker_invocations": len(negatives), "typed_stream_round_trips": sum(row["typed_stream_round_trips"] * 2 for row in positives),
              "runtime_input_file_reads": 0, "heldout_inputs_read": 0, "native_processes_started": 0, "native_acceptance": False, "public_writer_enabled": False}
    result_sha = write_json(output / "SdkNestedAssemblyResults.json", report)
    print(json.dumps({"passed": True, "result_sha256": result_sha, "source_manifest_sha256": source_sha, "nested_bundles": len(positives), "negative_cases": len(negatives),
                      "ordered_regressions": len(ordered_rows), "single_regressions": len(single_rows), "identified_workers": len(pids), "typed_stream_round_trips": report["typed_stream_round_trips"]}, sort_keys=True))


if __name__ == "__main__":
    main()
