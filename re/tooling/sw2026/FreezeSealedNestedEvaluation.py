from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PureWindowsPath
from shutil import copyfile

from AuthorCurves import digest, require, write_json
from InspectGeneratedNestedAssembly import SOURCE_LOCK, TOOLS as NATIVE_TOOLS
from NestedAssemblySourcePlan import ORACLE, checked


SCRIPT = Path(__file__).resolve()
CHECKOUT = SCRIPT.parents[3]
SCHEMA = "kit.sw2026.sealed-nested-writer-evaluation.v1"
WRITER_REVISION = "aa245b58e0dc9857f07e68aafa9727925ec52386"
WRITER_EVIDENCE = "2539defed11f4fffd6c84d4caf0297895b5f24d1fb1cb6f123b83dd1b5840560"
SOURCE_PHASE = "24278b6cace1ca57aedb1f90db5cbad394001f5e4521d3618fbf9356f3879dec"
FIRST_NATIVE = "539cb901df420671788475640ad5f097d673c48027a2754bea1e01396e908158"
REPEATED_PACKET = "13c6f53da57a592e12304281f4cd6b025a60b5aab6f1df23ea3748d29c49cde1"
TOOLS = (*NATIVE_TOOLS, "RunSealedNestedSourcePhase.py", "SealedNestedAssemblyPlan.py", "SealedNestedEvaluationState.py",
         "InspectSealedNestedAssembly.py", "RunSealedNestedEvaluation.py", SCRIPT.name)
EXTRA_SOURCE = ("re/tooling/sw2026/NestedAssemblyBundleProcess.py", "re/tooling/sw2026/PredictNestedAssembly.py",
                "tests/Convert/Solidworks/Research/ConstructionGuard.py", "tests/Convert/Solidworks/Research/FreshPartInput.py",
                "tests/Convert/Solidworks/Research/Assembly/RootRequest.py")


def guest_locator(value, name=None, fixed=False):
    path = PureWindowsPath(value)
    require(path.is_absolute() and ".." not in path.parts and (name is None or path.name == name), "invalid public guest locator")
    if fixed:
        require(re.fullmatch(r"[A-Za-z]:", path.drive) and len(path.parts) > 1, "evaluation artifacts require a private guest-local drive")
    return str(path)


def qualify_discovery(data, packet_sha, writer_hashes):
    require(data["passed"] is True and data["controls_healthy"] is True and data["distinct_processes"] == 4 and
            data["bracket_order_verified"] is True and data["generated_input_files_immutable"] is True and data["synchronized_derivative_files_match"] is True and
            data["heldout_inputs_read"] == 0 and data["source_lock_sha256"] == SOURCE_LOCK and data["writer_revision"] == WRITER_REVISION and
            data["writer_tool_sha256"] == writer_hashes and data["packet_sha256"] == packet_sha,
            "sealed execution requires both fully qualified disclosed native layouts from the pinned writer")
    rows = data["phases"]
    require([row["mode"] for row in rows] == ["before", "generated", "reopen", "after"] and all(row["passed"] is True for row in rows) and
            len({row["oracle_identity"]["process_creation_filetime"] for row in rows}) == 4 and
            all(row["oracle_identity"]["sha256"] == ORACLE for row in rows), "discovery native brackets or identities differ")


def code_sources():
    paths = set()
    for name in ("src", "re/tooling/sw2026/builders", "re/tooling/sw2026/serial"):
        base = CHECKOUT / name
        paths.update(path for path in base.rglob("*.py") if "__pycache__" not in path.parts)
    paths.update(CHECKOUT / name for name in EXTRA_SOURCE)
    for name in EXTRA_SOURCE:
        if name.startswith("tests/"):
            parent = (CHECKOUT / name).parent
            while parent != CHECKOUT:
                if (parent / "__init__.py").is_file():
                    paths.add(parent / "__init__.py")
                parent = parent.parent
    require(all(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(CHECKOUT) for path in paths),
            "the frozen code closure must contain ordinary repository Python sources")
    return sorted(paths)


def prepare(args):
    output = args.output.resolve()
    require(output.parent.is_dir() and not output.exists() and not output.is_relative_to(CHECKOUT), "choose an unused private sealed evaluation packet")
    source_phase = json.loads(checked(args.source_phase, SOURCE_PHASE).read_bytes())
    source_lock_path = CHECKOUT / "re/solidworks/v2026/heldout/NestedAssemblySourceLock01.json"
    source_lock = json.loads(checked(source_lock_path, SOURCE_LOCK, CHECKOUT).read_bytes())
    evidence_path = CHECKOUT / "re/solidworks/measurements/2026/GeneratedNestedAssemblyBundle01.json"
    evidence = json.loads(checked(evidence_path, WRITER_EVIDENCE, CHECKOUT).read_bytes())
    require(source_lock["passed"] is True and source_lock["heldout_payloads_read"] == 0 and source_lock["sealed_phase_packet_sha256"] == SOURCE_PHASE and
            source_phase["source_deck_sha256"] == source_lock["source_deck_sha256"] and all(row["heldout_source_locked"] is True for row in source_lock["slots"]),
            "both sealed native sources must be locked before writer evaluation")
    first = json.loads(checked(args.first_result, FIRST_NATIVE).read_bytes())
    repeated = json.loads(checked(args.repeat_result, args.repeat_sha256).read_bytes())
    qualify_discovery(first, first["packet_sha256"], evidence["writer_tool_sha256"])
    qualify_discovery(repeated, REPEATED_PACKET, evidence["writer_tool_sha256"])
    for name, sha in evidence["writer_tool_sha256"].items():
        checked(SCRIPT.parent / name, sha, SCRIPT.parent)
    for name, sha in source_lock["tool_sha256"].items():
        checked(SCRIPT.parent / name, sha, SCRIPT.parent)
    source_guest = guest_locator(args.source_phase_guest, "SealedPhases.json")
    private_base = guest_locator(args.guest_private_base, fixed=True)
    disclosed = guest_locator(args.disclosed_results, "Results")
    output.mkdir()
    (output / "Tools").mkdir()
    code_root = output / "CodeRoot"
    code_root.mkdir()
    hashes = {}
    for source in code_sources():
        relative = source.relative_to(CHECKOUT).as_posix()
        target = code_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(source, target)
        hashes[relative] = digest(target)
    code_manifest = output / "CodeManifest.json"
    write_json(code_manifest, {"schema": "kit.sw2026.frozen-nested-writer-code.v1", "writer_revision": WRITER_REVISION, "files_sha256": hashes})
    tool_hashes = {}
    for name in TOOLS:
        target = output / "Tools" / name
        copyfile(SCRIPT.parent / name, target)
        tool_hashes[name] = digest(target)
    inputs = ((args.source_phase, "SourcePhase.json"), (source_lock_path, "SourceLock.json"), (evidence_path, "WriterEvidence.json"),
              (args.first_result, "FirstDiscovery.json"), (args.repeat_result, "RepeatedDiscovery.json"))
    for source, name in inputs:
        copyfile(source, output / name)
    packet = output / "Evaluation.json"
    write_json(packet, {"schema": SCHEMA, "oracle_sha256": ORACLE, "writer_revision": WRITER_REVISION,
                        "writer_evidence_sha256": WRITER_EVIDENCE, "writer_tool_sha256": evidence["writer_tool_sha256"],
                        "code_manifest_sha256": digest(code_manifest), "tools_sha256": tool_hashes, "source_lock_sha256": SOURCE_LOCK,
                        "source_phase_sha256": SOURCE_PHASE, "source_phase_guest": source_guest, "guest_private_base": private_base,
                        "disclosed_results_guest": disclosed, "first_discovery_sha256": FIRST_NATIVE,
                        "repeated_discovery_sha256": args.repeat_sha256, "host_heldout_payloads_read": 0,
                        "sealed_results": True, "native_acceptance": False})
    sha = digest(packet)
    subprocess.run([sys.executable, "-B", str(output / "Tools/RunSealedNestedEvaluation.py"), "verify", str(packet), "--packet-sha256", sha],
                   check=True, capture_output=True, timeout=90)
    return {"packet": str(packet), "packet_sha256": sha, "code_manifest_sha256": digest(code_manifest), "tools_sha256": tool_hashes,
            "host_heldout_payloads_read": 0}


def main():
    parser = argparse.ArgumentParser(description="Freeze writer code and disclosed acceptance before any guest-only sealed request exposure")
    parser.add_argument("output", type=Path)
    for name in ("--source-phase", "--first-result", "--repeat-result"):
        parser.add_argument(name, required=True, type=Path)
    for name in ("--source-phase-guest", "--guest-private-base", "--disclosed-results", "--repeat-sha256"):
        parser.add_argument(name, required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
