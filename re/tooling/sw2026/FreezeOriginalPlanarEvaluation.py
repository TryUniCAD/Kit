import argparse
import json
from pathlib import Path
from shutil import copyfile
import subprocess
import sys

from AuthorCurves import digest, require, write_json
from OriginalPlanarEvaluation import DISCLOSED_NATIVE, PUBLIC_READ, SCHEMA, SOURCE_LOCK, SOURCE_SPECS, TOOLS, ORACLE, checked, verify_locators


def freeze(args):
    output = args.output.resolve()
    require(output.parent.is_dir() and not output.exists(), "choose a fresh private source-unexposed original-evaluation packet")
    proof = args.method_proof.resolve(strict=True)
    method = json.loads(checked(proof / "Result.json", args.method_result_sha256).read_bytes())
    require(method["passed"] and method["heldout_inputs_read"] == method["native_processes_started"] == 0, "the disclosed method rehearsal must pass before freezing source exposure")
    manifest_path = checked(proof / "SourceManifest.json", method["source_manifest_sha256"])
    manifest = json.loads(manifest_path.read_bytes())
    source_lock = Path(__file__).resolve().parents[3] / "re/solidworks/v2026/heldout/AssemblyPlanarMateSourceLock01.json"
    checked(source_lock, SOURCE_LOCK)
    native = checked(args.disclosed_native.resolve(strict=True), DISCLOSED_NATIVE)
    public = checked(args.disclosed_public_read.resolve(strict=True), PUBLIC_READ)
    locator_data = json.loads(args.locators.resolve(strict=True).read_bytes())
    verify_locators(locator_data)
    control = json.loads(args.control_case.resolve(strict=True).read_bytes())
    control = {key: control[key] for key in ("case", "child_size_m")}
    output.mkdir()
    code_root = output / "CodeRoot"
    code_root.mkdir()
    for name, row in manifest["files"].items():
        source = checked(proof / "CodeRoot" / name, row["sha256"])
        target = code_root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(source, target)
    copyfile(manifest_path, output / "CodeManifest.json")
    dependencies = output / "Dependencies"
    dependencies.mkdir()
    dependency_hashes = {}
    checkout = Path(__file__).resolve().parents[3]
    for name in ("pyproject.toml", "uv.lock"):
        copyfile(checkout / name, dependencies / name)
        dependency_hashes[name] = digest(dependencies / name)
    write_json(output / "DependencyLock.json", {"files_sha256": dependency_hashes})
    for source, name in ((proof / "Result.json", "MethodResult.json"), (native, "DisclosedNative.json"), (public, "DisclosedPublicRead.json"), (source_lock, "SourceLock.json")):
        copyfile(source, output / name)
    write_json(output / "Locators.json", locator_data)
    write_json(output / "ControlCase.json", control)
    tools = output / "Tools"
    tools.mkdir()
    tool_hashes = {}
    script_root = Path(__file__).resolve().parent
    drivers = {"OriginalPlanarEvaluation.py", "FreezeOriginalPlanarEvaluation.py", "RunOriginalPlanarEvaluation.py", "InspectOriginalPlanarSlot.py"}
    for name in TOOLS:
        prior = proof / "CodeRoot/re/tooling/sw2026" / name
        source = prior if prior.is_file() and name not in drivers else script_root / name
        copyfile(source, tools / name)
        tool_hashes[name] = digest(tools / name)
    packet = output / "Evaluation.json"
    write_json(packet, {"schema": SCHEMA, "oracle_sha256": ORACLE, "source_lock_sha256": SOURCE_LOCK, "specs_sha256": SOURCE_SPECS,
                        "method_result_sha256": args.method_result_sha256, "method_source_manifest_sha256": method["source_manifest_sha256"],
                        "code_manifest_sha256": digest(output / "CodeManifest.json"), "tools_sha256": tool_hashes,
                        "dependency_lock_sha256": digest(output / "DependencyLock.json"),
                        "locators_sha256": digest(output / "Locators.json"), "control_case_sha256": digest(output / "ControlCase.json"),
                        "source_access_requires_explicit_release": True, "heldout_inputs_read": 0, "native_acceptance": False})
    packet_sha = digest(packet)
    result = subprocess.run([sys.executable, "-B", str(tools / "RunOriginalPlanarEvaluation.py"), "verify", str(packet), "--packet-sha256", packet_sha], capture_output=True, timeout=90)
    (output / "HostVerify.stdout").write_bytes(result.stdout)
    (output / "HostVerify.stderr").write_bytes(result.stderr)
    require(result.returncode == 0, "the source-unexposed host method verification failed: " + result.stderr.decode()[-1800:])
    return {"packet": str(packet), "packet_sha256": packet_sha, "code_manifest_sha256": digest(output / "CodeManifest.json"), "tools_sha256": tool_hashes, "heldout_inputs_read": 0, "native_processes_started": 0}


def main():
    parser = argparse.ArgumentParser()
    for name in ("method-proof", "disclosed-native", "disclosed-public-read", "locators", "control-case", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--method-result-sha256", required=True)
    print(json.dumps(freeze(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
