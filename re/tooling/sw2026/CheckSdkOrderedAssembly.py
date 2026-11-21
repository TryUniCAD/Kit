import argparse
from itertools import permutations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from CheckSdkPlanar import digest, freeze_source, write_json
from CheckHeaderEpoch import compare_old
from CheckSdkAssembly import worker, one_case


def ordered_case(root, output, request, tag):
    built, build_id = worker(root, output, request, tag + "Build", "SdkOrderedAssemblyProcess.py")
    projected = {"request": request, "build": built}
    prepared, prepare_id = worker(root, output, projected, tag + "Prepare", "SdkAssemblyVerify.py")
    counterpart, counterpart_id = worker(root, output, projected, tag + "Counterpart", "SdkAssemblyCounterpart.py")
    if len(built["mate_classes"]) != len(request["mates"]) or built["wrapper_next_id"] != 2 * len(request["mates"]):
        raise ValueError("ordered generated graph omitted mate or wrapper state")
    return {"case": tag, "passed": True, "kind_order": [row["kind"] for row in request["mates"]], "mate_classes": built["mate_classes"], "mate_ids": built["mate_ids"],
            "dimension_ids": built["dimension_ids"], "next_id": built["next_id"], "wrapper_next_id": built["wrapper_next_id"],
            "assembly": {key: built["assembly"][key] for key in ("bytes", "sha256", "stream_order")}, "child": {key: built["child"][key] for key in ("bytes", "sha256", "stream_order")},
            "streams": prepared["assembly"], "round_trips": prepared["round_trips"], "checks": prepared["checks"],
            "same_as_independent_research": counterpart["same_as_independent_research"], "build": build_id, "prepare": prepare_id, "counterpart": counterpart_id}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--single-proof", type=Path, required=True)
    parser.add_argument("--planar-proof", type=Path, required=True)
    parser.add_argument("--distance-proof", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root, source, source_sha = freeze_source(args.root.resolve(), output)
    sys.path[:0] = [str(root), str(root / "src"), str(root / "re/tooling/sw2026")]
    from tests.Convert.Solidworks.Research.Construction.AssemblySets.MakeOrderCase import MakeOrderCase
    from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmCase import MakeAsmCase
    from SdkOrderedFaults import FAULTS
    positives = []
    for order in permutations(("coincident", "parallel", "distance")):
        for variant in (False, True):
            tag = "".join(kind[0].upper() for kind in order) + ("Beta" if variant else "Alpha")
            positives.append(ordered_case(root, output, MakeOrderCase(order, variant), tag))
    negatives = []
    for index, fault in enumerate(FAULTS):
        request = {"request": MakeOrderCase(("distance", "coincident", "parallel"), False), "fault": fault}
        result, identity = worker(root, output, request, f"Reject{index:02}", "SdkOrderedFaultProcess.py")
        if not result["rejected"] or not result["actual_parent_state_unchanged"] or result["writer_output_count"]:
            raise ValueError("ordered prior state did not reject atomically")
        negatives.append({"case": fault, "passed": True, "exception": result["exception"], "diagnostic": result["diagnostic"], "actual_parent_state_unchanged": True, "before": result["before"], "after": result["after"], "identity": identity})
    prior_bytes = (args.single_proof / "SdkAssemblyResults.json").read_bytes()
    prior = json.loads(prior_bytes)
    single_cases = []
    for old in prior["positive_cases"]:
        variant = old["case"].endswith("Beta")
        current = one_case(root, output, MakeAsmCase(old["kind"], old["axis"], variant), "Single" + old["case"])
        if any(current[key] != old[key] for key in ("assembly", "child", "streams", "checks", "next_id", "wrapper_next_id")):
            raise ValueError("ordered continuation changed the published single mate path")
        single_cases.append(current)
    regressions = [compare_old(root, output, args.planar_proof, "planar", source), compare_old(root, output, args.distance_proof, "distance", source)]
    for name, row in source["files"].items():
        if digest((root / name).read_bytes()) != row["sha256"]:
            raise ValueError("ordered frozen source changed during process proof")
    pids = [row[phase]["worker_pid"] for row in (*positives, *single_cases) for phase in ("build", "prepare", "counterpart")]
    pids.extend(row["identity"]["worker_pid"] for row in negatives)
    pids.extend(row["identity"]["worker_pid"] for group in regressions for row in group["cases"])
    if len(pids) != len(set(pids)):
        raise ValueError("ordered proof reused process identity")
    report = {"schema": "kit.sw2026.sdk-ordered-assembly.v1", "passed": True, "source_manifest_sha256": source_sha, "source_files": len(source["files"]),
              "source_locked_before_generation": True, "source_unchanged": True, "positive_cases": positives, "negative_cases": negatives,
              "single_bundle_regressions": single_cases, "single_raw_result_sha256": digest(prior_bytes), "published_regressions": regressions,
              "distinct_worker_processes": len(pids), "typed_stream_round_trips": sum(row["round_trips"] for row in (*positives, *single_cases)),
              "runtime_input_file_reads": 0, "native_processes_started": 0, "heldout_inputs_read": 0, "native_acceptance": False, "public_writer_enabled": False}
    report_sha = write_json(output / "SdkOrderedAssemblyResults.json", report)
    print(json.dumps({"passed": True, "report_sha256": report_sha, "source_manifest_sha256": source_sha, "ordered_bundles": len(positives), "atomic_negatives": len(negatives),
                      "single_bundle_regressions": len(single_cases), "historical_bundle_regressions": sum(len(group["cases"]) for group in regressions), "distinct_workers": len(pids), "typed_stream_round_trips": report["typed_stream_round_trips"]}, sort_keys=True))


if __name__ == "__main__":
    main()
