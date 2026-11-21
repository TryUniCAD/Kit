from __future__ import annotations

import argparse
from base64 import b64decode
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import subprocess
import sys

from AuthorCurves import digest, require
from InspectSdkNestedAssembly import AUTHORED, ORACLE, SCHEMA, SOURCE, SOURCE_LOCK, TOOLS, checked
from SdkNestedExpectations import prediction, verify_prediction


SCRIPT = Path(__file__).resolve()
CHECKOUT = SCRIPT.parents[3]


def write(path, value):
    data = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with path.open("xb") as output:
        output.write(data)
    return digest(path)


def windows_path(path):
    return str(PureWindowsPath(r"\\Mac\Home") / path.resolve(strict=True).relative_to(Path.home()))


def prepare(args):
    proof = args.proof.resolve(strict=True)
    source_path = checked(proof / "SourceManifest.json", args.source_manifest_sha256, proof)
    source = json.loads(source_path.read_bytes())
    code_root = proof / "CodeRoot"
    for name, row in source["files"].items():
        checked(code_root / name, row["sha256"], code_root)
    result_path = proof / "SdkNestedAssemblyResults.json"
    result = json.loads(result_path.read_bytes())
    require(result["passed"] and result["source_manifest_sha256"] == args.source_manifest_sha256
            and result["source_locked_before_generation"] and result["source_unchanged"]
            and len(result["positive_cases"]) == 2 and len(result["ordered_regressions"]) == 12 and len(result["single_regressions"]) == 18,
            "the frozen complete SDK nested construction proof is not qualified")
    output = args.output.resolve()
    require(not output.is_relative_to(CHECKOUT) and output.parent.is_dir() and not output.exists(), "choose an unused private native packet outside the checkout")
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(code_root), str(code_root / "src")]
    from tests.Convert.Solidworks.Research.Construction.Nesting.MakeNestedCase import MakeNestedCase

    target = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover") / output.name / "GeneratedInput"
    request = MakeNestedCase(args.mixed, str(target))
    expected = prediction(request, "plate", args.edit_depth_m)
    require(verify_prediction(request, expected) == target, "independent native prediction changed the encoded working directory")
    output.mkdir()
    request_bytes = json.dumps(request, separators=(",", ":"), allow_nan=False).encode()
    (output / "NeutralRequest.json").write_bytes(request_bytes)
    expected_sha = write(output / "Prediction.json", expected)
    builds = []
    for label in ("BuildA", "BuildB"):
        execution = subprocess.run([sys.executable, "-I", "-B", str(code_root / "re/tooling/sw2026/SdkNestedAssemblyProcess.py"), str(code_root)],
                                   input=request_bytes, capture_output=True, timeout=120)
        (output / (label + ".stdout")).write_bytes(execution.stdout)
        (output / (label + ".stderr")).write_bytes(execution.stderr)
        require(execution.returncode == 0, "the frozen SDK nested build failed: " + execution.stderr.decode()[-3000:])
        build = json.loads(execution.stdout)
        require(build["passed"] and build["runtime_input_file_reads"] == build["sdk_runtime_research_imports"] == 0, "nested build crossed the declared process boundary")
        builds.append(build)
    first, second = (dict(row) for row in builds)
    require(first.pop("worker_pid") != second.pop("worker_pid") and first == second, "the complete SDK nested bundle differs across fresh processes")
    frozen = output / "FrozenGenerated"
    frozen.mkdir()
    files = {}
    for key, row in first["documents"].items():
        name = expected["definitions"][key]["file"]
        data = b64decode(row["blob"], validate=True)
        (frozen / name).write_bytes(data)
        require(digest(frozen / name) == row["sha256"] and len(data) == row["bytes"], "the generated nested artifact identity differs")
        files[key] = {"file": name, "encoded_path": str(target / name), "bytes": row["bytes"], "sha256": row["sha256"]}
    copyfile(source_path, output / "SourceManifest.json")
    copyfile(result_path, output / "SourceProcessResult.json")
    copyfile(CHECKOUT / "re/solidworks/v2026/heldout/NestedAssemblySourceLock01.json", output / "SourceLock.json")
    checked(output / "SourceLock.json", SOURCE_LOCK, output)
    fixture = {"schema": "kit.sw2026.sdk-nested-native-fixture.v1", "source_manifest_sha256": args.source_manifest_sha256,
               "source_process_result_sha256": digest(result_path), "source_code_root": str(code_root), "request_sha256": digest(output / "NeutralRequest.json"),
               "prediction_sha256": expected_sha, "preparer_sha256": digest(SCRIPT), "files": files,
               "build_sha256": {name: digest(output / (name + ".stdout")) for name in ("BuildA", "BuildB")},
               "typed_stream_round_trips_per_build": first["typed_stream_round_trips"], "source_observations_used_by_generation": 0,
               "heldout_inputs_read": 0, "native_processes_started": 0, "native_acceptance": False}
    fixture_sha = write(output / "Fixture.json", fixture)
    tools = output / "Tools"
    tools.mkdir()
    hashes = {}
    for name in TOOLS:
        copyfile(SCRIPT.parent / name, tools / name)
        hashes[name] = digest(tools / name)
    tools_sha = write(output / "ToolsManifest.json", {"schema": "kit.sw2026.sdk-nested-native-tools.v1", "files": hashes})
    control = "N02MixedRepeated" if args.mixed else "N01NestedSingle"
    packet_sha = write(output / "Packet.json", {"schema": SCHEMA, "oracle_sha256": ORACLE, "fixture_sha256": fixture_sha,
                                               "source_lock_sha256": SOURCE_LOCK, "control": control, "control_author_sha256": AUTHORED[control],
                                               "tools_sha256": hashes, "tools_manifest_sha256": tools_sha, "heldout_inputs_read": 0, "native_acceptance": False})
    observer = windows_path(tools / "InspectSdkNestedAssembly.py")
    packet = windows_path(output / "Packet.json")
    common = ["py", "-3.11", observer]
    tail = ["--packet-sha256", packet_sha]
    recipe = {"schema": "kit.sw2026.sdk-nested-native-recipe.v1", "packet_sha256": packet_sha,
              "verify_argv": [*common, "verify", packet, *tail],
              "phase_argv": {name: [*common, "run", packet, name, *tail] for name in ("before", "generated", "reopen", "after")},
              "summary_argv": [*common, "summarize", packet, *tail], "result_windows_path": str(PureWindowsPath(packet).parent / "Inspection/Result.json"),
              "trailing_control_required_even_on_failure": True, "encoded_working_directory": str(target), "heldout_inputs_read": 0, "native_processes_started": 0}
    recipe_sha = write(output / "Recipe.json", recipe)
    preflight = subprocess.run([sys.executable, "-B", str(tools / "InspectSdkNestedAssembly.py"), "verify", str(output / "Packet.json"), *tail],
                               capture_output=True, timeout=45)
    (output / "HostPreflight.stdout").write_bytes(preflight.stdout)
    (output / "HostPreflight.stderr").write_bytes(preflight.stderr)
    require(preflight.returncode == 0, "the no-COM native packet preflight failed: " + preflight.stderr.decode()[-3000:])
    return {"packet": str(output / "Packet.json"), "packet_sha256": packet_sha, "fixture_sha256": fixture_sha,
            "prediction_sha256": expected_sha, "tools_manifest_sha256": tools_sha, "recipe_sha256": recipe_sha,
            "observer_sha256": hashes["InspectSdkNestedAssembly.py"], "files": files, "native_processes_started": 0}


def main():
    parser = argparse.ArgumentParser(description="Freeze a complete generated SDK nested bundle and its independent native lifecycle recipe")
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--source-manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mixed", action="store_true")
    parser.add_argument("--edit-depth-m", type=float, default=0.011375)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
