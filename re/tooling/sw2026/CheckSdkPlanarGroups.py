import argparse
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from CheckSdkPlanar import digest, freeze_source, write_json
from CheckSdkAssembly import one_case, worker
from CheckSdkOrderedAssembly import ordered_case
from CheckSdkNestedAssembly import nested_case


def require(value, message):
    if not value:
        raise ValueError(message)


def group_request(request):
    result = {key: deepcopy(request[key]) for key in ("assembly", "child", "occurrences")}
    values = request.get("mates", [request.get("mate")])
    result["fixed_occurrence"] = values[0]["fixed_occurrence"]
    result["mates"] = []
    for row in values:
        mate = {"kind": row["kind"], "name": row["name"], "endpoints": [{"occurrence": index, "axis": row["axis"]} for index in range(2)]}
        if row["kind"] == "distance":
            mate.update({key: row[key] for key in ("distance_m", "design_intent", "selected_leader")})
        result["mates"].append(mate)
    return result


def group_case(root, output, request, tag):
    first, first_id = worker(root, output, request, tag + "BuildA", "SdkPlanarGroupProcess.py")
    second, second_id = worker(root, output, request, tag + "BuildB", "SdkPlanarGroupProcess.py")
    a, b = dict(first), dict(second)
    require(a.pop("worker_pid") != b.pop("worker_pid") and a == b, "complete planar group builds differ across fresh processes")
    counterpart, counterpart_id = worker(root, output, {"request": request, "build": first}, tag + "Counterpart", "SdkAssemblyCounterpart.py")
    require(counterpart["same_as_independent_research"], "the complete group differs from its independent mathematical composer")
    return {"case": tag, "passed": True, "occurrence_count": first["occurrence_count"], "mate_count": first["mate_count"], "endpoints": first["endpoints"],
            "assembly": {key: first["assembly"][key] for key in ("bytes", "sha256", "stream_order")},
            "child": {key: first["child"][key] for key in ("bytes", "sha256", "stream_order")}, "proofs": first["proofs"], "round_trips": first["round_trips"] * 2,
            "fixed_indices": first["fixed_indices"], "next_id": first["next_id"], "wrapper_next_id": first["wrapper_next_id"],
            "same_as_independent_research": True, "builds": [first_id, second_id, counterpart_id]}


def main():
    parser = argparse.ArgumentParser()
    for name in ("root", "output", "ordered-proof", "single-proof", "nested-proof"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root, source, source_sha = freeze_source(args.root.resolve(), output)
    sys.path[:0] = [str(root), str(root / "src"), str(root / "re/tooling/sw2026")]
    from tests.Convert.Solidworks.Research.Construction.PlanarGroups.GroupCaseInput import GroupCaseInput
    from tests.Convert.Solidworks.Research.Construction.PlanarGroups.GroupFaultCase import GroupFaultCase
    from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmCase import MakeAsmCase
    from tests.Convert.Solidworks.Research.Construction.AssemblySets.MakeOrderCase import MakeOrderCase

    positives, pids = [], []
    for count in (2, 3, 5):
        for variant in (False, True):
            tag = f"Group{count}" + ("Beta" if variant else "Alpha")
            row = group_case(root, output, GroupCaseInput(count, variant), tag)
            positives.append(row)
            pids.extend(item["worker_pid"] for item in row["builds"])
    negatives = []
    for fault in ("missing_endpoint", "same_occurrence", "cross_axis", "same_name", "zero_distance", "wrong_distance", "fixed_missing", "extra_state"):
        data = json.dumps(GroupFaultCase(fault), separators=(",", ":"), allow_nan=False).encode()
        result = subprocess.run([sys.executable, "-I", "-B", str(root / "re/tooling/sw2026/SdkPlanarGroupProcess.py"), str(root)], input=data, capture_output=True, timeout=120)
        (output / ("Reject" + fault + ".stdout")).write_bytes(result.stdout)
        (output / ("Reject" + fault + ".stderr")).write_bytes(result.stderr)
        require(result.returncode != 0 and not result.stdout and b"ValueError" in result.stderr and b"PermissionError" not in result.stderr, "unsupported group input escaped fail-closed publication")
        negatives.append({"case": fault, "passed": True, "exit_code": result.returncode, "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr), "writer_output_count": 0})
    regressions = []
    for kind, directory, filename in (("ordered", args.ordered_proof, "SdkOrderedAssemblyResults.json"), ("single", args.single_proof, "SdkAssemblyResults.json")):
        old = json.loads((directory / filename).read_bytes())
        for row in old["positive_cases"]:
            variant = row["case"].endswith("Beta")
            request = MakeOrderCase(tuple(row["kind_order"]), variant) if kind == "ordered" else MakeAsmCase(row["kind"], row["axis"], variant)
            tag = "Prior" + row["case"]
            current = ordered_case(root, output, request, tag) if kind == "ordered" else one_case(root, output, request, tag)
            require(all(current[key] == row[key] for key in ("assembly", "child", "streams", "checks", "next_id", "wrapper_next_id")), "prior complete assembly bytes or owned graph changed")
            alternate, identity = worker(root, output, group_request(request), tag + "Group", "SdkPlanarGroupProcess.py")
            require(all(alternate[target][key] == row[target][key] for target in ("assembly", "child") for key in ("bytes", "sha256", "stream_order")), "the explicit group pair changed established complete bundle bytes")
            current["group_identity"] = identity
            current["group_round_trips"] = alternate["round_trips"]
            regressions.append(current)
            pids.extend(current[name]["worker_pid"] for name in ("build", "prepare", "counterpart"))
            pids.append(identity["worker_pid"])
    old = json.loads((args.nested_proof / "SdkNestedAssemblyResults.json").read_bytes())
    nested = []
    for row in old["positive_cases"]:
        request = json.loads((args.nested_proof / (row["case"] + "BuildARequest.json")).read_bytes())
        current = nested_case(root, output, request, "PriorNested" + row["case"])
        require(all(current[key] == row[key] for key in ("definition_count", "expanded_root_occurrences", "typed_stream_round_trips", "documents")), "recursive complete bundle bytes changed")
        nested.append(current)
        pids.extend(item["worker_pid"] for item in current["builds"])
    require(len(pids) == len(set(pids)), "group proof reused an identified successful worker")
    require(all(digest((root / name).read_bytes()) == row["sha256"] for name, row in source["files"].items()), "frozen group source changed during qualification")
    report = {"schema": "kit.sw2026.sdk-planar-groups-construction.v1", "passed": True, "source_manifest_sha256": source_sha, "source_files": len(source["files"]),
              "source_locked_before_generation": True, "source_unchanged": True, "positive_cases": positives, "negative_cases": negatives, "prior_flat_bundles": regressions,
              "prior_nested_bundles": nested, "distinct_identified_workers": len(pids), "negative_worker_invocations": len(negatives),
              "typed_stream_round_trips": sum(row["round_trips"] for row in positives) + sum(row["round_trips"] + row["group_round_trips"] for row in regressions) + sum(row["typed_stream_round_trips"] * 2 for row in nested),
              "runtime_input_file_reads": 0, "heldout_inputs_read": 0, "native_processes_started": 0, "native_acceptance": False, "public_writer_enabled": False}
    result_sha = write_json(output / "SdkPlanarGroupResults.json", report)
    print(json.dumps({"passed": True, "source_manifest_sha256": source_sha, "result_sha256": result_sha, "positive_groups": len(positives), "negative_cases": len(negatives),
                      "flat_regressions": len(regressions), "nested_regressions": len(nested), "identified_workers": len(pids), "typed_stream_round_trips": report["typed_stream_round_trips"]}, sort_keys=True))


if __name__ == "__main__":
    main()
