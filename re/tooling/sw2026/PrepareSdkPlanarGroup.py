import argparse
from base64 import b64decode
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import subprocess
import sys

from AuthorCurves import digest, require
from InspectSdkPlanarGroup import CONTROL_CHILD, CONTROL_PARENT, ORACLE, SCHEMA, TOOLS, checked
from SdkPlanarGroupPrediction import predict


def write(path, value):
    with path.open("xb") as output:
        output.write((json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    return digest(path)


def windows_path(path):
    return str(PureWindowsPath(r"\\Mac\Home") / path.resolve(strict=True).relative_to(Path.home()))


def prepare(args):
    proof = args.proof.resolve(strict=True)
    manifest = json.loads(checked(proof / "SourceManifest.json", args.source_manifest_sha256).read_bytes())
    code_root = proof / "CodeRoot"
    for name, row in manifest["files"].items():
        checked(code_root / name, row["sha256"])
    source_result = proof / "SdkPlanarGroupResults.json"
    result = json.loads(source_result.read_bytes())
    require(result["passed"] and result["source_manifest_sha256"] == args.source_manifest_sha256 and result["heldout_inputs_read"] == 0, "the complete frozen group construction proof is not qualified")
    output = args.output.resolve()
    require(not output.exists() and output.parent.is_dir(), "choose a fresh private disclosed group packet")
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(code_root), str(code_root / "src")]
    from tests.Convert.Solidworks.Research.Construction.PlanarGroups.GroupCaseInput import GroupCaseInput

    request = GroupCaseInput(3, False)
    target = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover") / output.name / "GeneratedInput"
    parent_name = request["assembly"]["name"] + ".SLDASM"
    child_name = PureWindowsPath(request["child"]["settings"]["output"]["path_name"]).name
    request["assembly"]["output"]["path_name"] = str(target / parent_name)
    request["child"]["settings"]["output"]["path_name"] = str(target / child_name)
    for index, row in enumerate(request["occurrences"]):
        row["name"] = PureWindowsPath(child_name).stem + "-" + str(index + 1)
    planes = request["child"]["settings"]["system"]["planes"]
    case = {"name": request["assembly"]["name"], "split": "discovery", "fixed_occurrence": request["fixed_occurrence"],
            "placements": [{"axis": "z", "angle_deg": 17., "translation_m": row["origin"]} for row in request["occurrences"]],
            "mates": [{"kind": row["kind"], "name": row["name"], "planes": [[end["occurrence"], planes[end["axis"]]] for end in row["endpoints"]], **({"distance_m": row["distance_m"]} if row["kind"] == "distance" else {})} for row in request["mates"]]}
    distance, = [row["distance_m"] for row in request["mates"] if row["kind"] == "distance"]
    expected = predict(request, case, distance + .01573)
    control = json.loads(args.control_case.resolve(strict=True).read_bytes())
    control = {key: control[key] for key in ("case", "child_size_m")}
    parent = checked(args.control_parent.resolve(strict=True), CONTROL_PARENT)
    child = checked(args.control_child.resolve(strict=True), CONTROL_CHILD)
    output.mkdir()
    incoming = json.dumps(request, separators=(",", ":"), allow_nan=False).encode()
    (output / "NeutralRequest.json").write_bytes(incoming)
    expected_sha = write(output / "Prediction.json", expected)
    builds = []
    for name in ("BuildA", "BuildB", "Counterpart"):
        entry = "SdkAssemblyCounterpart.py" if name == "Counterpart" else "SdkPlanarGroupProcess.py"
        data = json.dumps({"request": request, "build": builds[0]}, allow_nan=False).encode() if name == "Counterpart" else incoming
        execution = subprocess.run([sys.executable, "-I", "-B", str(code_root / "re/tooling/sw2026" / entry), str(code_root)], input=data, capture_output=True, timeout=120)
        (output / (name + ".stdout")).write_bytes(execution.stdout)
        (output / (name + ".stderr")).write_bytes(execution.stderr)
        require(execution.returncode == 0, "the frozen SDK group build failed: " + execution.stderr.decode()[-3000:])
        row = json.loads(execution.stdout)
        require(row["passed"] and row["runtime_input_file_reads"] == 0, "group staging crossed the declared construction boundary")
        builds.append(row)
    a, b = dict(builds[0]), dict(builds[1])
    require(a.pop("worker_pid") != b.pop("worker_pid") and a == b and builds[2]["same_as_independent_research"], "complete group files differ between guarded or independent builds")
    frozen = output / "FrozenGenerated"
    frozen.mkdir()
    files = {}
    for key, name in (("assembly", parent_name), ("child", child_name)):
        blob = b64decode(builds[0][key]["blob"], validate=True)
        (frozen / name).write_bytes(blob)
        files[key] = {"file": name, "bytes": len(blob), "sha256": digest(frozen / name), "encoded_path": str(target / name)}
    fixture = {"schema": "kit.sw2026.sdk-explicit-group-native-fixture.v1", "source_manifest_sha256": args.source_manifest_sha256,
               "source_process_result_sha256": digest(source_result), "request_sha256": digest(output / "NeutralRequest.json"), "prediction_sha256": expected_sha,
               "phase_sha256": {name: digest(output / (name + ".stdout")) for name in ("BuildA", "BuildB", "Counterpart")},
               "files": files, "runtime_input_file_reads": 0, "heldout_inputs_read": 0, "native_acceptance": False}
    fixture_sha = write(output / "Fixture.json", fixture)
    copyfile(proof / "SourceManifest.json", output / "SourceManifest.json")
    copyfile(source_result, output / "SourceProcessResult.json")
    control_sha = write(output / "ControlCase.json", control)
    tools = output / "Tools"
    tools.mkdir()
    hashes = {}
    for name in TOOLS:
        copyfile(Path(__file__).resolve().parent / name, tools / name)
        hashes[name] = digest(tools / name)
    packet_sha = write(output / "Packet.json", {"schema": SCHEMA, "oracle_sha256": ORACLE, "fixture_sha256": fixture_sha,
                                               "tools_sha256": hashes, "control_case_sha256": control_sha,
                                               "control": {"parent": {"host_path": str(parent), "windows_path": windows_path(parent)}, "child": {"host_path": str(child), "windows_path": windows_path(child)}},
                                               "heldout_inputs_read": 0, "native_acceptance": False})
    common = ["py", "-3.11", "-B", windows_path(tools / "InspectSdkPlanarGroup.py")]
    packet = windows_path(output / "Packet.json")
    recipe_sha = write(output / "Recipe.json", {"verify_argv": [*common, "verify", packet, "--packet-sha256", packet_sha],
                                               "run_argv": [*common, "run", packet, "--packet-sha256", packet_sha], "result_windows_path": str(PureWindowsPath(packet).parent / "Inspection/Result.json"),
                                               "packet_sha256": packet_sha, "native_processes_started": 0, "heldout_inputs_read": 0})
    execution = subprocess.run([sys.executable, "-B", str(tools / "InspectSdkPlanarGroup.py"), "verify", str(output / "Packet.json"), "--packet-sha256", packet_sha], capture_output=True, timeout=45)
    (output / "HostPreflight.stdout").write_bytes(execution.stdout)
    (output / "HostPreflight.stderr").write_bytes(execution.stderr)
    require(execution.returncode == 0, "the no-COM group preflight failed: " + execution.stderr.decode()[-3000:])
    return {"packet": str(output / "Packet.json"), "packet_sha256": packet_sha, "fixture_sha256": fixture_sha,
            "recipe_sha256": recipe_sha, "observer_sha256": hashes["InspectSdkPlanarGroup.py"], "prediction_sha256": expected_sha, "files": files, "native_processes_started": 0}


def main():
    parser = argparse.ArgumentParser()
    for name in ("proof", "control-case", "control-parent", "control-child", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-manifest-sha256", required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
