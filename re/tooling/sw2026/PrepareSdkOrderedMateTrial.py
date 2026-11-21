from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile

from InspectSdkOrderedMates import CONTROL_CHILD, CONTROL_PARENT, ORACLE, SCHEMA, TOOLS, checked
from SdkOrderedMateExpectations import verify_predictions


def write(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as output:
        output.write(data)
    return hashlib.sha256(data).hexdigest()


def windows_path(path):
    return str(PureWindowsPath(r"\\Mac\Home") / path.resolve(strict=True).relative_to(Path.home()))


def prepare(args):
    source = args.fixture.resolve(strict=True).parent
    fixture = json.loads(checked(args.fixture, args.fixture_sha256).read_bytes())
    prediction = json.loads(checked(source / "Prediction.json", fixture["prediction_sha256"]).read_bytes())
    request = json.loads(checked(source / "NeutralRequest.json", fixture["request_sha256"]).read_bytes())
    verify_predictions(request, prediction)
    control_parent = checked(args.control_parent, CONTROL_PARENT)
    control_child = checked(args.control_child, CONTROL_CHILD)
    control_request = args.control_case.resolve(strict=True)
    raw_control = json.loads(control_request.read_bytes())
    control = {key: raw_control[key] for key in ("case", "child_size_m")}
    if control["case"]["name"] != "A22CombinedRotated" or control["case"]["split"] != "discovery" or control["child_size_m"] != [0.04, 0.02, 0.01]:
        raise ValueError("expected the qualified disclosed A22 case and its own authored child")
    proof = Path(fixture["source_code_root"]).parent / "SdkOrderedAssemblyResults.json"
    checked(proof, fixture["source_process_result_sha256"])
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    for name in ("Fixture.json", "Prediction.json", "NeutralRequest.json", "SourceManifest.json"):
        copyfile(source / name, output / name)
    copyfile(proof, output / "SourceProcessResult.json")
    for name, value in fixture["phase_sha256"].items():
        copyfile(checked(source / (name + ".stdout"), value), output / (name + ".stdout"))
    frozen = output / "FrozenGenerated"
    frozen.mkdir()
    for name, row in fixture["files"].items():
        copyfile(checked(source / "FrozenGenerated" / name, row["sha256"]), frozen / name)
    tool_source = Path(__file__).resolve().parent
    tools = output / "Tools"
    tools.mkdir()
    hashes = {}
    for name in TOOLS:
        copyfile(tool_source / name, tools / name)
        hashes[name] = hashlib.sha256((tools / name).read_bytes()).hexdigest()
    tools_sha = write(output / "ToolsManifest.json", {"schema": "kit.sw2026.sdk-ordered-observer-tools.v1", "files": hashes})
    case_sha = write(output / "ControlCase.json", control)
    job = {"schema": SCHEMA, "oracle_sha256": ORACLE, "fixture_sha256": args.fixture_sha256,
           "tools_sha256": hashes, "tools_manifest_sha256": tools_sha, "control_case_sha256": case_sha,
           "control_recipe_sha256": hashlib.sha256(control_request.read_bytes()).hexdigest(),
           "control": {"parent": {"host_path": str(control_parent), "windows_path": windows_path(control_parent), "sha256": CONTROL_PARENT},
                       "child": {"host_path": str(control_child), "windows_path": windows_path(control_child), "sha256": CONTROL_CHILD}},
           "heldout_inputs_read": 0, "source_before_execution": True, "native_acceptance": False,
           "scope": "disclosed fully SDK generated rotated ordered coincident distance parallel group with synchronized save and fresh reopen"}
    packet_sha = write(output / "Packet.json", job)
    native_script = windows_path(tools / "InspectSdkOrderedMates.py")
    native_packet = windows_path(output / "Packet.json")
    recipe = {"schema": "kit.sw2026.sdk-ordered-native-recipe.v1", "packet_sha256": packet_sha,
              "verify_argv": ["py", "-3.11", native_script, "verify", native_packet, "--packet-sha256", packet_sha],
              "run_argv": ["py", "-3.11", native_script, "run", native_packet, "--packet-sha256", packet_sha],
              "result_windows_path": str(PureWindowsPath(native_packet).parent / "Inspection" / "Result.json"),
              "encoded_generated_paths": [row["encoded_path"] for row in fixture["files"].values()],
              "native_processes_started": 0, "heldout_inputs_read": 0}
    recipe_sha = write(output / "Recipe.json", recipe)
    return {"packet": str(output / "Packet.json"), "packet_sha256": packet_sha, "tools_manifest_sha256": tools_sha,
            "fixture_sha256": args.fixture_sha256, "recipe_sha256": recipe_sha, "observer_sha256": hashes["InspectSdkOrderedMates.py"],
            "expectations_sha256": hashes["SdkOrderedMateExpectations.py"], "native_processes_started": 0}


def main():
    parser = argparse.ArgumentParser(description="Freeze an ordered SDK mate observer without starting CAD")
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--fixture-sha256", required=True)
    parser.add_argument("--control-case", type=Path, required=True)
    parser.add_argument("--control-parent", type=Path, required=True)
    parser.add_argument("--control-child", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
