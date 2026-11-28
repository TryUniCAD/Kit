import argparse
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


A22_PARENT = "fac5708432e569e787dfc00aa87fe08e5ef2d6830ec88f2d69525f8030d9fd1f"
A22_CHILD = "b46e1e0f066db55730ce765cb2547b97ad1416e1ea0ceaa588bb8e819f727321"
GROUP_PARENT = "1522aa21cb3f39db16a6b082088fef0a0063acf6a53df6cb31c479137761eda3"
GROUP_CHILD = "1d158e0f67507587a2cb5056f103f34dbc930138b4f43ee5d20359c6329dbfcc"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return sha256(value).hexdigest()


def write(path, value):
    value = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(value)
    return digest(value)


def leaves(value):
    if isinstance(value, dict):
        return [item for row in value.values() for item in leaves(row)]
    if isinstance(value, list):
        return [item for row in value for item in leaves(row)]
    return [value]


def no_recorded_state(value):
    if isinstance(value, dict):
        require(not {"$bytes", "record_data", "solidworks_source_bytes", "typed_archive_owner"} & set(value), "source-native recorded state crossed the semantic translation boundary")
        for row in value.values():
            no_recorded_state(row)
    if isinstance(value, (list, tuple)):
        for row in value:
            no_recorded_state(row)


def worker(root, output, incoming, name, entry, extra=(), rejecting=False, expected_error=b"ValueError"):
    data = json.dumps(incoming, separators=(",", ":"), allow_nan=False).encode()
    write(output / (name + "Input.json"), incoming)
    args = [sys.executable, "-I", "-B", str(root / "re/tooling/sw2026" / entry), *extra]
    result = subprocess.run(args, input=data, capture_output=True, timeout=120)
    (output / (name + ".stdout")).write_bytes(result.stdout)
    (output / (name + ".stderr")).write_bytes(result.stderr)
    identity = {"input_sha256": digest(data), "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr), "exit_code": result.returncode}
    if rejecting:
        require(result.returncode != 0 and not result.stdout and expected_error in result.stderr and b"PermissionError" not in result.stderr, "the unsupported semantic request escaped fail-closed publication")
        return None, identity
    require(result.returncode == 0, name + " failed: " + result.stderr.decode()[-2000:])
    value = json.loads(result.stdout)
    require(value.get("passed", True) and not value.get("runtime_input_file_reads") and not value.get("com_imports"), "the semantic rehearsal crossed its process boundary")
    identity["worker_pid"] = value["worker_pid"]
    return value, identity


def load_disclosed(path, parent_hash, child_hash):
    record = json.loads(path.read_bytes())
    require(record["input_sha256"] == parent_hash and record["com_imports"] == [], "the declared public source document custody differs")
    from interchange import CadDocument

    document = CadDocument.from_json(record["document_json"])
    document.assert_valid()
    require(document.assembly.documents[0].document.source.sha256 == child_hash, "the disclosed source linked a different actual child")
    return record, document


def one_case(root, output, name, record, document, case, dimensions):
    from ReadSdkPlanarGroupNative import compare

    native_target = "\\\\Mac\\Home\\Documents\\UniCAD\\Oracle121Takeover\\OriginalPlanarMethod" + name + "\\GeneratedInput\\"
    incoming = {"document_json": record["document_json"], "case": case, "dimensions_m": dimensions,
                "output": {"assembly_path": native_target + case["name"] + ".SLDASM", "child_path": native_target + "CohortChild.SLDPRT"}}
    first, first_id = worker(root, output, incoming, name + "SemanticA", "OriginalPlanarProcess.py", ("--root", str(root)))
    second, second_id = worker(root, output, incoming, name + "SemanticB", "OriginalPlanarProcess.py", ("--root", str(root)))
    a, b = dict(first), dict(second)
    require(a.pop("worker_pid") != b.pop("worker_pid") and a == b, "the names and independently authored request changed between fresh semantic workers")
    require(all(type(value) is str for value in leaves(first["names"])), "the names-only projection contains captured numeric or binary state")
    no_recorded_state(first["request"])
    source_comparison = compare(document, first["prediction"], False, document.assembly.documents[0].document.source.sha256)
    built, built_id = worker(root, output, first["request"], name + "BuildA", "SdkPlanarGroupProcess.py", (str(root),))
    again, again_id = worker(root, output, first["request"], name + "BuildB", "SdkPlanarGroupProcess.py", (str(root),))
    a, b = dict(built), dict(again)
    require(a.pop("worker_pid") != b.pop("worker_pid") and a == b, "complete SDK files differ between semantic rehearsal builds")
    counterpart, counterpart_id = worker(root, output, {"request": first["request"], "build": built}, name + "Counterpart", "SdkAssemblyCounterpart.py", (str(root),))
    require(counterpart["same_as_independent_research"], "the full original-recipe bundle differs from the independent mathematical composer")
    frozen = output / (name + "Generated")
    frozen.mkdir()
    parent = frozen / (case["name"] + ".SLDASM")
    child = frozen / "CohortChild.SLDPRT"
    parent.write_bytes(b64decode(built["assembly"]["blob"], validate=True))
    child.write_bytes(b64decode(built["child"]["blob"], validate=True))
    read, read_id = worker(root, output, {}, name + "PublicRead", "ReadSdkPlanarGroupNative.py", ("read", "--root", str(root), "--file", str(parent)))
    from interchange import CadDocument

    read_document = CadDocument.from_json(read["document_json"])
    generated_comparison = compare(read_document, first["prediction"], False, built["child"]["sha256"])
    require(digest(parent.read_bytes()) == built["assembly"]["sha256"] and digest(child.read_bytes()) == built["child"]["sha256"], "the strict SDK read changed generated inputs")
    row = {"case": name, "passed": True, "source_parent_sha256": record["input_sha256"], "source_child_sha256": document.assembly.documents[0].document.source.sha256,
           "names_sha256": write(output / (name + "Names.json"), first["names"]), "request_sha256": write(output / (name + "Request.json"), first["request"]),
           "prediction_sha256": write(output / (name + "Prediction.json"), first["prediction"]), "source_semantic_comparison": source_comparison, "generated_public_comparison": generated_comparison,
           "generated_files": {key: {field: built[key][field] for field in ("sha256", "bytes")} for key in ("assembly", "child")},
           "same_as_independent_research": True, "typed_stream_round_trips": built["round_trips"] + again["round_trips"],
           "names_only_strings": True, "writer_request_contains_no_recorded_state": True, "processes": [first_id, second_id, built_id, again_id, counterpart_id, read_id]}
    return row, incoming


def fault_request(incoming, name):
    value = deepcopy(incoming)
    source = json.loads(value["document_json"])
    assembly = source["assembly"]
    if name == "changed_recipe_pose":
        value["case"]["placements"][1]["translation_m"][0] += .0001473
    elif name == "wrong_recipe_endpoint":
        value["case"]["mates"][0]["planes"][0][0] = 1
    elif name == "extra_mate_state":
        value["case"]["mates"][0]["suppressed"] = True
    elif name == "virtual_source_component":
        assembly["instances"]["$tuple"][0]["attributes"]["virtual"] = True
    elif name == "missing_source_child_driver":
        assembly["documents"]["$tuple"][0]["document"]["parameters"]["$tuple"].pop()
    elif name == "colliding_actual_names":
        assembly["mates"]["$tuple"][0]["name"] = assembly["instances"]["$tuple"][0]["name"]
    elif name == "nonprincipal_source_frame":
        assembly["documents"]["$tuple"][0]["document"]["support_planes"]["$tuple"][0]["transform"]["origin"]["z"] = .1473
    else:
        raise ValueError("unknown process negative")
    value["document_json"] = json.dumps(source, separators=(",", ":"), allow_nan=False)
    return value


def main():
    parser = argparse.ArgumentParser()
    for name in ("root", "a22-read", "a22-case", "n3-read", "n3-prediction", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    require(not output.exists(), "choose a fresh disclosed-only method proof directory")
    output.mkdir()
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(root), str(root / "src"), str(root / "re/tooling/sw2026")]
    from CheckSdkPlanar import freeze_source

    frozen, manifest, source_hash = freeze_source(root, output)
    sys.path[:0] = [str(frozen), str(frozen / "src"), str(frozen / "re/tooling/sw2026")]
    paths = [args.a22_read.resolve(strict=True), args.a22_case.resolve(strict=True), args.n3_read.resolve(strict=True), args.n3_prediction.resolve(strict=True)]
    input_hashes = [digest(path.read_bytes()) for path in paths]
    a22, a22_doc = load_disclosed(paths[0], A22_PARENT, A22_CHILD)
    a22_case = json.loads(paths[1].read_bytes())
    require(a22_case["child_size_m"] == [.04, .02, .01] and a22_case["case"]["name"] == "A22CombinedRotated", "the disclosed independent common-child recipe differs")
    n3, n3_doc = load_disclosed(paths[2], GROUP_PARENT, GROUP_CHILD)
    n3_prediction = json.loads(paths[3].read_bytes())
    require(n3_prediction["case"]["name"] == "SdkPlanarGroup3Alpha", "the disclosed group recipe differs")
    rows = []
    row, incoming = one_case(frozen, output, "A22", a22, a22_doc, a22_case["case"], a22_case["child_size_m"])
    rows.append(row)
    row, _ = one_case(frozen, output, "N3", n3, n3_doc, n3_prediction["case"], [n3_prediction["child_dimensions_m"][key] for key in ("width", "height", "depth")])
    rows.append(row)
    negatives = []
    for fault in ("changed_recipe_pose", "wrong_recipe_endpoint", "extra_mate_state", "virtual_source_component", "missing_source_child_driver", "colliding_actual_names", "nonprincipal_source_frame"):
        error = b"CadDocumentValidationError" if fault == "missing_source_child_driver" else b"ValueError"
        _, identity = worker(frozen, output, fault_request(incoming, fault), "Reject" + fault, "OriginalPlanarProcess.py", ("--root", str(frozen)), True, error)
        negatives.append({"case": fault, "passed": True, "writer_output_count": 0, "identity": identity})
    identities = [item["worker_pid"] for row in rows for item in row["processes"]]
    require(len(set(identities)) == len(identities), "the method rehearsal reused a successful worker identity")
    require([digest(path.read_bytes()) for path in paths] == input_hashes, "the method rehearsal changed disclosed source evidence")
    require(all(digest((frozen / name).read_bytes()) == item["sha256"] for name, item in manifest["files"].items()), "the frozen method closure changed during rehearsal")
    report = {"schema": "kit.sw2026.original-planar-method-rehearsal.v1", "passed": True, "source_manifest_sha256": source_hash,
              "source_files": len(manifest["files"]), "source_frozen_before_semantic_projection": True, "source_unchanged": True,
              "inputs_unchanged": True, "input_sha256": input_hashes, "cases": rows, "negative_cases": negatives,
              "distinct_successful_workers": len(identities), "rejecting_worker_invocations": len(negatives),
              "typed_stream_round_trips": sum(row["typed_stream_round_trips"] for row in rows), "runtime_input_file_reads_during_projection_and_construction": 0,
              "heldout_inputs_read": 0, "native_processes_started": 0, "heldout_acceptance": False, "public_assembly_writer_enabled": False}
    result_hash = write(output / "Result.json", report)
    print(json.dumps({"passed": True, "result_sha256": result_hash, "source_manifest_sha256": source_hash, "successful_workers": len(identities), "rejected_inputs": len(negatives), "typed_stream_round_trips": report["typed_stream_round_trips"], "heldout_inputs_read": 0, "native_processes_started": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
